from time import perf_counter
from asyncio import sleep
from bot import app
from info import COMMAND_HANDLER
from pyrogram import enums, filters
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.forbidden_403 import ChatWriteForbidden
from pyrogram.errors.exceptions.bad_request_400 import ChatAdminRequired, UserAdminInvalid

@app.on_message(filters.incoming & ~filters.private & filters.command(['inkick'], COMMAND_HANDLER))
async def inkick(_, message):
  user = await app.get_chat_member(message.chat.id, message.from_user.id)
  if user.status in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
    if len(message.command) > 1:
      input_str = message.command
      sent_message = message.reply_text("🚮**Sedang membersihkan user, mungkin butuh waktu beberapa saat...**")
      count = 0
      async for member in app.get_chat_members(message.chat.id):
        if member.user.status in input_str and not member.status in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
          try:
            await app.ban_chat_member(message.chat.id, member.user.id, int(time() + 45))
            count += 1
            await sleep(1)
          except (ChatAdminRequired, UserAdminInvalid):
            await sent_message.edit("❗**Oh tidaakk, saya bukan admin disini**\n__Saya pergi dari sini, tambahkan aku kembali dengan perijinan banned pengguna.__")
            await app.leave_chat(message.chat.id)
            break
          except FloodWait as e:
            await sleep(e.value)
      try:
        await sent_message.edit("✔️ **Berhasil menendang {} pengguna berdasarkan argumen.**".format(count))
      except ChatWriteForbidden:
        pass
    else:
      await message.reply_text("❗ **Arguments Required**\n__See /inkickhelp in personal message for more information.__")
  else:
    sent_message = await message.reply_text("❗ **You have to be the group creator to do that.**")
    await sleep(5)
    await sent_message.delete()

@app.on_message(filters.incoming & ~filters.private & filters.command(['dkick'], COMMAND_HANDLER))
async def dkick(client, message):
  user = await app.get_chat_member(message.chat.id, message.from_user.id)
  if user.status in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
    sent_message = message.reply_text("🚮**Sedang membersihkan user, mungkin butuh waktu beberapa saat...**")
    count = 0
    async for member in app.get_chat_members(message.chat.id):
      if member.user.is_deleted and not member.status in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
        try:
          await app.ban_chat_member(message.chat.id, member.user.id, int(time() + 45))
          count += 1
          await sleep(1)
        except (ChatAdminRequired, UserAdminInvalid):
          await sent_message.edit("❗**Oh tidaakk, saya bukan admin disini**\n__Saya pergi dari sini, tambahkan aku kembali dengan perijinan banned pengguna.__")
          await app.leave_chat(message.chat.id)
          break
        except FloodWait as e:
          await sleep(e.value)
    try:
      await sent_message.edit("✔️ **Berhasil menendang {} akun terhapus.**".format(count))
    except ChatWriteForbidden:
      pass
  else:
    sent_message = await message.reply_text("❗ **Kamu harus jadi admin atau owner grup untuk melakukan tindakan ini.**")
    await sleep(5)
    await sent_message.delete()
    
@app.on_message(filters.incoming & ~filters.private & filters.command(['instatus'], COMMAND_HANDLER))
async def instatus(client, message):
  start_time = perf_counter()
  user = await app.get_chat_member(message.chat.id, message.from_user.id)
  count = await app.get_chat_members_count(message.chat.id)
  if user.status in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
    sent_message = await message.reply_text("**Sedang mengumpulkan informasi pengguna...**")
    recently = 0
    within_week = 0
    within_month = 0
    long_time_ago = 0
    deleted_acc = 0
    premium_acc = 0
    no_username = 0
    restricted = 0
    banned = 0
    uncached = 0
    bot = 0
    async for ban in app.get_chat_members(message.chat.id, filter=enums.ChatMembersFilter.BANNED):
      banned += 1
    async for restr in app.get_chat_members(message.chat.id, filter=enums.ChatMembersFilter.RESTRICTED):
      restricted += 1
    async for member in app.get_chat_members(message.chat.id):
      user = member.user
      if user.is_deleted:
        deleted_acc += 1
      elif user.is_bot:
        bot += 1
      elif user.is_premium:
        premium_acc += 1
      elif not user.username:
        no_username += 1
      elif user.status == enums.UserStatus.RECENTLY:
        recently += 1
      elif user.status == enums.UserStatus.LAST_WEEK:
        within_week += 1
      elif user.status == enums.UserStatus.LAST_MONTH:
        within_month += 1
      elif user.status == enums.UserStatus.LONG_AGO:
        long_time_ago += 1
      else:
        uncached += 1
    end_time = perf_counter()
    timelog = "{:.2f}".format(end_time - start_time)
    await sent_message.edit("<b>💠 {}\n👥 {} Anggota\n——————\n👁‍🗨 Informasi Status Anggota\n——————\n</b>🕒 <code>recently</code>: {}\n🕒 <code>within_week</code>: {}\n🕒 <code>within_month</code>: {}\n🕒 <code>long_time_ago</code>: {}\n🉑 Tanpa Username: {}\n🤐 Dibatasi: {}\n🚫 Diblokir: {}\n👻 Deleted Account (<code>/dkick</code>): {}\n🤖 Bot: {}\n⭐️ Premium User: {}\n👽 UnCached: {}\n\n⏱ Waktu eksekusi {} detik.".format(message.chat.title, count, recently, within_week, within_month, long_time_ago, no_username, restricted, banned, deleted_acc, bot, premium_acc, uncached, timelog))
