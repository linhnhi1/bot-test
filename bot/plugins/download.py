import time
import asyncio
import math
import os
import logging
from bot import app
from pySmartDL import SmartDL
from datetime import datetime
from bot.utils.decorator import capture_err
from info import COMMAND_HANDLER
from pyrogram import filters
from bot.utils.pyro_progress import (
    progress_for_pyrogram,
    humanbytes,
)

@app.on_message(filters.command(["download","download@MissKatyRoBot"], COMMAND_HANDLER) & filters.user(617426792))
@capture_err
async def download(client, message):
    pesan = await message.reply_text("Processing...", quote=True)
    if message.reply_to_message is not None:
        start_t = datetime.now()
        c_time = time.time()
        the_real_download_location = await client.download_media(
            message=message.reply_to_message,
            progress=progress_for_pyrogram,
            progress_args=("trying to download, sabar yakk..", pesan, c_time),
        )
        end_t = datetime.now()
        ms = (end_t - start_t).seconds
        await pesan.edit(
            f"Downloaded to <code>{the_real_download_location}</code> in <u>{ms}</u> seconds."
        )
    elif len(message.command) > 1:
        start_t = datetime.now()
        the_url_parts = " ".join(message.command[1:])
        url = the_url_parts.strip()
        custom_file_name = os.path.basename(url)
        if "|" in the_url_parts:
            url, custom_file_name = the_url_parts.split("|")
            url = url.strip()
            custom_file_name = custom_file_name.strip()
        download_file_path = os.path.join("./dl/", custom_file_name)
        downloader = SmartDL(url, download_file_path, progress_bar=False)
        downloader.start(blocking=False)
        c_time = time.time()
        while not downloader.isFinished():
            total_length = downloader.filesize if downloader.filesize else None
            downloaded = downloader.get_dl_size()
            display_message = ""
            now = time.time()
            diff = now - c_time
            percentage = downloader.get_progress() * 100
            speed = downloader.get_speed()
            elapsed_time = round(diff) * 1000
            progress_str = "[{0}{1}]\nProgress: {2}%".format(
                "".join(["█" for i in range(math.floor(percentage / 5))]),
                "".join(["░" for i in range(20 - math.floor(percentage / 5))]),
                round(percentage, 2),
            )
            estimated_total_time = downloader.get_eta(human=True)
            try:
                current_message = "trying to download\n"
                current_message += f"URL: {url}\n"
                current_message += f"File Name: {custom_file_name}\n"
                current_message += f"{progress_str}\n"
                current_message += (
                    f"{humanbytes(downloaded)} of {humanbytes(total_length)}\n"
                )
                current_message += f"ETA: {estimated_total_time}"
                if round(diff % 10.00) == 0 and current_message != display_message:
                    await pesan.edit(
                        disable_web_page_preview=True, text=current_message
                    )
                    display_message = current_message
                    await asyncio.sleep(10)
            except Exception as e:
                logging.info(str(e))
                pass
        if os.path.exists(download_file_path):
            end_t = datetime.now()
            ms = (end_t - start_t).seconds
            await pesan.edit(
                f"Downloaded to <code>{download_file_path}</code> in {ms} seconds"
            )
    else:
        await pesan.edit("Reply to a Telegram Media, to download it to my local server.")
