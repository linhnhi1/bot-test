from datetime import datetime, timedelta
import time
import os
import logging
from misskaty.helper.http import http
from pyrogram import enums, filters
from pyrogram.types import ChatMemberUpdated, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import ChatSendMediaForbidden, MessageTooLong, RPCError, SlowmodeWait
from misskaty import app
from misskaty.core.decorator.errors import capture_err, asyncify
from PIL import Image, ImageChops, ImageDraw, ImageFont
import textwrap
from database.users_chats_db import db
from utils import temp
from pyrogram.errors import ChatAdminRequired
from misskaty.vars import SUDO, LOG_CHANNEL, SUPPORT_CHAT, COMMAND_HANDLER

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
LOGGER = logging.getLogger(__name__)

def circle(pfp, size=(215, 215)):
    pfp = pfp.resize(size, Image.ANTIALIAS).convert("RGBA")
    bigsize = (pfp.size[0] * 3, pfp.size[1] * 3)
    mask = Image.new("L", bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(pfp.size, Image.ANTIALIAS)
    mask = ImageChops.darker(mask, pfp.split()[-1])
    pfp.putalpha(mask)
    return pfp


def draw_multiple_line_text(image, text, font, text_start_height):
    """
    From unutbu on [python PIL draw multiline text on image](https://stackoverflow.com/a/7698300/395857)
    """
    draw = ImageDraw.Draw(image)
    image_width, image_height = image.size
    y_text = text_start_height
    lines = textwrap.wrap(text, width=50)
    for line in lines:
        line_width, line_height = font.getsize(line)
        draw.text(((image_width - line_width) / 2, y_text), line, font=font, fill="black")
        y_text += line_height


@asyncify
def welcomepic(pic, user, chat, count, id):
    background = Image.open("img/bg.png")  # <- Background Image (Should be PNG)
    background = background.resize((1024, 500), Image.ANTIALIAS)
    pfp = Image.open(pic).convert("RGBA")
    pfp = circle(pfp)
    pfp = pfp.resize((265, 265))  # Resizes the Profilepicture so it fits perfectly in the circle
    font = ImageFont.truetype("Calistoga-Regular.ttf", 37)  # <- Text Font of the Member Count. Change the text size for your preference
    member_text = f"User#{count}, Selamat Datang {user}"  # <- Text under the Profilepicture with the Membercount
    draw_multiple_line_text(background, member_text, font, 395)
    draw_multiple_line_text(background, chat, font, 47)
    ImageDraw.Draw(background).text((530, 460), "Generated by @MissKatyRoBot", font=ImageFont.truetype("Calistoga-Regular.ttf", 28), size=20, align="right")
    background.paste(pfp, (379, 123), pfp)  # Pastes the Profilepicture on the Background Image
    background.save(f"downloads/welcome#{id}.png")  # Saves the finished Image in the folder with the filename
    return f"downloads/welcome#{id}.png"


@app.on_chat_member_updated(filters.group & filters.chat(-1001128045651))
async def member_has_joined(c: app, member: ChatMemberUpdated):
    if not member.new_chat_member or member.new_chat_member.status in {"banned", "left", "restricted"} or member.old_chat_member:
        return
    user = member.new_chat_member.user if member.new_chat_member else member.from_user
    if user.id in SUDO:
        await c.send_message(
            member.chat.id,
            "Waw, owner ku yang keren baru saja bergabung ke grup!",
        )
        return
    elif user.is_bot:
        return  # ignore bots
    else:
        if (temp.MELCOW).get(f"welcome-{member.chat.id}") is not None:
            try:
                await (temp.MELCOW[f"welcome-{member.chat.id}"]).delete()
            except:
                pass
        mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
        joined_date = datetime.fromtimestamp(time.time()).strftime("%Y.%m.%d %H:%M:%S")
        first_name = f"{user.first_name} {user.last_name}" if user.last_name else user.first_name
        id = user.id
        dc = user.dc_id if user.dc_id else "Member tanpa PP"
        count = await app.get_chat_members_count(member.chat.id)
        try:
            pic = await app.download_media(user.photo.big_file_id, file_name=f"pp{user.id}.png")
        except AttributeError:
            pic = "img/profilepic.png"
        welcomeimg = await welcomepic(pic, user.first_name, member.chat.title, count, user.id)
        temp.MELCOW[f"welcome-{member.chat.id}"] = await c.send_photo(
            member.chat.id,
            photo=welcomeimg,
            caption=f"Hai {mention}, Selamat datang digrup {member.chat.title} harap baca rules di pinned message terlebih dahulu.\n\n<b>Nama :<b> <code>{first_name}</code>\n<b>ID :<b> <code>{id}</code>\n<b>DC ID :<b> <code>{dc}</code>\n<b>Tanggal Join :<b> <code>{joined_date}</code>",
        )
        userspammer = ""
        # Spamwatch Detection
        try:
            headers = {"Authorization": "Bearer XvfzE4AUNXkzCy0DnIVpFDlxZi79lt6EnwKgBj8Quuzms0OSdHvf1k6zSeyzZ_lz"}
            apispamwatch = (await http.get(f"https://api.spamwat.ch/banlist/{user.id}", headers=headers)).json()
            if not apispamwatch.get("error"):
                await app.ban_chat_member(member.chat.id, user.id, datetime.now() + timedelta(seconds=30))
                userspammer += f"<b>#SpamWatch Federation Ban</b>\nUser {mention} [<code>{user.id}</code>] has been kicked because <code>{apispamwatch.get('reason')}</code>.\n"
        except Exception as err:
            LOGGER.error(f"ERROR in Spamwatch Detection. {err}")
        # Combot API Detection
        try:
            apicombot = (await http.get(f"https://api.cas.chat/check?user_id={user.id}")).json()
            if apicombot.get("ok") == "true":
                await app.ban_chat_member(member.chat.id, user.id, datetime.now() + timedelta(seconds=30))
                userspammer += f"<b>#CAS Federation Ban</b>\nUser {mention} [<code>{user.id}</code>] detected as spambot and has been kicked. Powered by <a href='https://api.cas.chat/check?user_id={user.id}'>Combot AntiSpam.</a>"
        except Exception as err:
            LOGGER.error(f"ERROR in Combot API Detection. {err}")
        if userspammer != "":
            await c.send_message(member.chat.id, userspammer)
        try:
            os.remove(f"downloads/welcome#{user.id}.png")
            os.remove(f"downloads/pp{user.id}.png")
        except Exception:
            pass


@app.on_message(filters.new_chat_members & filters.group)
async def save_group(bot, message):
    r_j_check = [u.id for u in message.new_chat_members]
    if temp.ME in r_j_check:
        if not await db.get_chat(message.chat.id):
            total = await bot.get_chat_members_count(message.chat.id)
            r_j = message.from_user.mention if message.from_user else "Anonymous"
            await bot.send_message(LOG_CHANNEL, "#NewGroup\nGroup = {}(<code>{}</code>)\nMembers Count = <code>{}</code>\nAdded by - {}".format(message.chat.title, message.chat.id, total, r_j))
            await db.add_chat(message.chat.id, message.chat.title)
        if message.chat.id in temp.BANNED_CHATS:
            # Inspired from a boat of a banana tree
            buttons = [[InlineKeyboardButton("Support", url=f"https://t.me/{SUPPORT_CHAT}")]]
            reply_markup = InlineKeyboardMarkup(buttons)
            k = await message.reply(
                text="<b>CHAT NOT ALLOWED 🐞\n\nMy admins has restricted me from working here ! If you want to know more about it contact support..</b>",
                reply_markup=reply_markup,
            )

            try:
                await k.pin()
            except:
                pass
            await bot.leave_chat(message.chat.id)
            return
        buttons = [[InlineKeyboardButton("ℹ️ Help", url=f"https://t.me/{temp.U_NAME}?start=help"), InlineKeyboardButton("📢 Updates", url="https://t.me/YasirPediaChannel")]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_text(text=f"<b>Terimakasih sudah menambahkan saya di {message.chat.title} ❣️\n\nJika ada kendala atau saran bisa kontak ke saya.</b>", reply_markup=reply_markup)
    else:
        for u in message.new_chat_members:
            count = await app.get_chat_members_count(message.chat.id)
            try:
                pic = await app.download_media(u.photo.big_file_id, file_name=f"pp{u.id}.png")
            except AttributeError:
                pic = "img/profilepic.png"
            welcomeimg = await welcomepic(pic, u.first_name, message.chat.title, count, u.id)
            if (temp.MELCOW).get(f"welcome-{message.chat.id}") is not None:
                try:
                    await (temp.MELCOW[f"welcome-{message.chat.id}"]).delete()
                except:
                    pass
            try:
                temp.MELCOW[f"welcome-{message.chat.id}"] = await app.send_photo(
                    message.chat.id,
                    photo=welcomeimg,
                    caption=f"Hai {u.mention}, Selamat datang digrup {message.chat.title}.",
                )
            except (ChatSendMediaForbidden, SlowmodeWait):
                await app.leave_chat(message.chat.id)
            try:
                os.remove(f"downloads/welcome#{u.id}.png")
                os.remove(f"downloads/pp{u.id}.png")
            except Exception:
                pass


@app.on_message(filters.command("leave") & filters.user(SUDO))
async def leave_a_chat(bot, message):
    if len(message.command) == 1:
        return await message.reply("Give me a chat id")
    chat = message.command[1]
    try:
        chat = int(chat)
    except:
        chat = chat
    try:
        buttons = [[InlineKeyboardButton("Support", url=f"https://t.me/{SUPPORT_CHAT}")]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await bot.send_message(
            chat_id=chat,
            text="<b>Hai kawan, \nOwner aku bilang saya harus pergi! Jika kamu ingin menambahkan bot ini lagi silahkan kontak owner bot ini.</b>",
            reply_markup=reply_markup,
        )
        await bot.leave_chat(chat)
    except Exception as e:
        await message.reply(f"Error - {e}")
        await bot.leave_chat(chat)


@app.on_message(filters.command("disable") & filters.user(SUDO))
async def disable_chat(bot, message):
    if len(message.command) == 1:
        return await message.reply("Give me a chat id")
    r = message.text.split(None)
    if len(r) > 2:
        reason = message.text.split(None, 2)[2]
        chat = message.text.split(None, 2)[1]
    else:
        chat = message.command[1]
        reason = "No reason Provided"
    try:
        chat_ = int(chat)
    except:
        return await message.reply("Give Me A Valid Chat ID")
    cha_t = await db.get_chat(chat_)
    if not cha_t:
        return await message.reply("Chat Not Found In DB")
    if cha_t["is_disabled"]:
        return await message.reply(f"This chat is already disabled:\nReason-<code> {cha_t['reason']} </code>")
    await db.disable_chat(chat_, reason)
    temp.BANNED_CHATS.append(chat_)
    await message.reply("Chat Succesfully Disabled")
    try:
        buttons = [[InlineKeyboardButton("Support", url=f"https://t.me/{SUPPORT_CHAT}")]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await bot.send_message(chat_id=chat_, text=f"<b>Hello Friends, \nMy admin has told me to leave from group so i go! If you wanna add me again contact my support group.</b> \nReason : <code>{reason}</code>", reply_markup=reply_markup)
        await bot.leave_chat(chat_)
    except Exception as e:
        await message.reply(f"Error - {e}")


@app.on_message(filters.command("enable") & filters.user(SUDO))
async def re_enable_chat(bot, message):
    if len(message.command) == 1:
        return await message.reply("Give me a chat id")
    chat = message.command[1]
    try:
        chat_ = int(chat)
    except:
        return await message.reply("Give Me A Valid Chat ID")
    sts = await db.get_chat(int(chat))
    if not sts:
        return await message.reply("Chat Not Found In DB !")
    if not sts.get("is_disabled"):
        return await message.reply("This chat is not yet disabled.")
    await db.re_enable_chat(chat_)
    temp.BANNED_CHATS.remove(chat_)
    await message.reply("Chat Succesfully re-enabled")


# a function for trespassing into others groups, Inspired by a Vazha
# Not to be used , But Just to showcase his vazhatharam.
# @app.on_message(filters.command('invite') & filters.user(SUDO))
async def gen_invite(bot, message):
    if len(message.command) == 1:
        return await message.reply("Give me a chat id")
    chat = message.command[1]
    try:
        chat = int(chat)
    except:
        return await message.reply("Give Me A Valid Chat ID")
    try:
        link = await bot.create_chat_invite_link(chat)
    except ChatAdminRequired:
        return await message.reply("Invite Link Generation Failed, Iam Not Having Sufficient Rights")
    except Exception as e:
        return await message.reply(f"Error {e}")
    await message.reply(f"Here is your Invite Link {link.invite_link}")


@app.on_message(filters.command(["adminlist", "adminlist@MissKatyRoBot"], COMMAND_HANDLER))
@capture_err
async def adminlist(_, message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return await message.reply("Perintah ini hanya untuk grup")
    try:
        administrators = []
        async for m in app.get_chat_members(message.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
            administrators.append(f"{m.user.first_name}")

        res = "".join(f"~ {i}\n" for i in administrators)
        return await message.reply(f"Daftar Admin di <b>{message.chat.title}</b> ({message.chat.id}):\n~ {res}")
    except Exception as e:
        await message.reply(f"ERROR: {str(e)}")


@app.on_message(filters.command(["kickme"], COMMAND_HANDLER))
@capture_err
async def kickme(_, message):
    reason = None
    if len(message.text.split()) >= 2:
        reason = message.text.split(None, 1)[1]
    try:
        await message.ban_member(message.from_user.id)
        txt = f"Pengguna {message.from_user.mention} menendang dirinya sendiri. Mungkin dia sedang frustasi 😕"
        txt += f"\n<b>Alasan</b>: {reason}" if reason else ""
        await message.reply_text(txt)
        await message.unban_member(message.from_user.id)
    except RPCError as ef:
        await message.reply_text(f"Sepertinya ada error, silahkan report ke owner saya. \nERROR: {str(ef)}")
    return


@app.on_message(filters.command("users") & filters.user(SUDO))
async def list_users(bot, message):
    # https://t.me/GetTGLink/4184
    raju = await message.reply("Getting List Of Users")
    users = await db.get_all_users()
    out = "Users Saved In DB Are:\n\n"
    async for user in users:
        out += f"<a href=tg://user?id={user['id']}>{user['name']}</a>"
        if user["ban_status"]["is_banned"]:
            out += "( Banned User )"
        out += "\n"
    try:
        await raju.edit_text(out)
    except MessageTooLong:
        with open("users.txt", "w+") as outfile:
            outfile.write(out)
        await message.reply_document("users.txt", caption="List Of Users")


@app.on_message(filters.command("chats") & filters.user(SUDO))
async def list_chats(bot, message):
    raju = await message.reply("Getting List Of chats")
    chats = await db.get_all_chats()
    out = "Chats Saved In DB Are:\n\n"
    async for chat in chats:
        out += f"**Title:** `{chat['title']}`\n**- ID:** `{chat['id']}`"
        if chat["chat_status"]["is_disabled"]:
            out += "( Disabled Chat )"
        out += "\n"
    try:
        await raju.edit_text(out)
    except MessageTooLong:
        with open("chats.txt", "w+") as outfile:
            outfile.write(out)
        await message.reply_document("chats.txt", caption="List Of Chats")
