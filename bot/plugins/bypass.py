import re
from bot.helper.http import http
from bot import app
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import MessageTooLong
from info import COMMAND_HANDLER
from bot.helper.tools import rentry
from urllib.parse import unquote
from bot.core.decorator.errors import capture_err
from bot.helper.human_read import get_readable_file_size

LIST_LINK = """
- Pling and all aliases.
- Other link soon...
"""

__MODULE__ = "Bypass"
__HELP__ = f"""
/directurl [Link] - Bypass URL.

Supported Link:
{LIST_LINK}
"""

async def pling_bypass(url):
    try:
        id_url = re.search(r"https?://(store.kde.org|www.pling.com)\/p\/(\d+)", url)[2]
        link = f"https://www.pling.com/p/{id_url}/loadFiles"
        res = await http.get(link)
        json_dic_files = res.json().pop("files")
        msg = f"\n**Source Link** :\n`{url}`\n**Direct Link :**\n"
        msg += "\n".join(f'**→ [{i["name"]}]({unquote(i["url"])}) ({get_readable_file_size(int(i["size"]))})**' for i in json_dic_files)
        return msg
    except Exception as e:
        return e

@app.on_message(filters.command(["directurl"], COMMAND_HANDLER))
@capture_err
async def bypass(_, message):
  if len(message.command) == 1:
    return await message.reply(f"Gunakan perintah /{message.command[0]} untuk bypass url")
  url = message.command[1]
  msg = "Bypassing URL.."
  mention = f"**Bypasser:** {message.from_user.mention} ({message.from_user.id})"
  if re.match(r"https?://(store.kde.org|www.pling.com)\/p\/(\d+)", url):
     data = await pling_bypass(url)
     try:
        await message.edit(f"**Bypassed URL:**\n{data}\n\n{mention}", quote=True)
     except MessageTooLong:
        result = rentry(data)
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("Open Link", url=result), InlineKeyboardButton("Raw Link", url=f"{result}/raw")]])
        await message.edit(f"**Bypassed URL:**\n{result}\n\nBecause your bypassed url is too long, so your link will be pasted to rentry.\n{mention}", reply_markup=markup, quote=True)
  else:
     await message.edit("Unsupported link..")
    
