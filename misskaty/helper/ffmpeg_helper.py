import asyncio
import os
import time

from pyrogram.errors import FloodWait
from pyrogram.types import InputMediaPhoto

from misskaty.plugins.dev import shell_exec


def hhmmss(seconds):
    """Chuyển đổi số giây thành định dạng HH:MM:SS"""
    return time.strftime("%H:%M:%S", time.gmtime(seconds))


async def take_ss(video_file):
    """Chụp ảnh màn hình từ video bằng VCSI"""
    out_put_file_name = f"genss-{str(time.time())}.png"
    cmd = f"""vcsi "{video_file}" -t -w 1340 -g 4x4 --timestamp-font assets/DejaVuSans.ttf --metadata-font assets/DejaVuSans-Bold.ttf --template misskaty/helper/ssgen_template.html --quality 100 --end-delay-percent 20 --metadata-font-size 30 -o {out_put_file_name} --timestamp-font-size 20"""
    await shell_exec(cmd)
    return out_put_file_name if os.path.lexists(out_put_file_name) else None


async def ssgen_link(video, output_directory, ttl):
    """Tạo ảnh chụp màn hình từ liên kết video bằng FFmpeg"""
    out_put_file_name = f"{output_directory}/{str(time.time())}.png"
    cmd = [
        "ffmpeg",
        "-ss",
        str(ttl),
        "-i",
        video,
        "-vframes",
        "1",
        "-f",
        "image2",
        out_put_file_name,
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()
    stderr.decode().strip()
    stdout.decode().strip()
    return out_put_file_name if os.path.isfile(out_put_file_name) else None


async def genss_link(msg, video_link, output_directory, min_duration, no_of_photos):
    """Tạo nhiều ảnh chụp màn hình từ liên kết video"""
    metadata = (
        await shell_exec(
            f"ffprobe -i {video_link} -show_entries format=duration -v quiet -of csv='p=0'"
        )
    )[0]
    duration = round(float(metadata))
    if duration > min_duration:
        images = []
        ttl_step = duration // no_of_photos
        current_ttl = ttl_step
        for looper in range(no_of_photos):
            ss_img = await ssgen_link(video_link, output_directory, current_ttl)
            images.append(
                InputMediaPhoto(
                    media=ss_img, caption=f"Ảnh chụp tại {hhmmss(current_ttl)}"
                )
            )
            try:
                await msg.edit(
                    f"📸 <b>Chụp ảnh màn hình:</b>\n<code>{looper+1} trên {no_of_photos} ảnh đã tạo..</code>"
                )
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await msg.edit(
                    f"📸 <b>Chụp ảnh màn hình:</b>\n<code>{looper+1} trên {no_of_photos} ảnh đã tạo..</code>"
                )
            current_ttl = current_ttl + ttl_step
            await asyncio.sleep(2)
        return images
    else:
        return None
