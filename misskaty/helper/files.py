"""
Giấy phép MIT (MIT License)
Bản quyền (c) 2021 TheHamkerCat

Cho phép bất kỳ cá nhân nào nhận được bản sao của phần mềm này và các tệp tài liệu liên quan (gọi chung là "Phần mềm") được quyền sử dụng miễn phí mà không có bất kỳ hạn chế nào, bao gồm nhưng không giới hạn quyền sử dụng, sao chép, chỉnh sửa, hợp nhất, xuất bản, phân phối, cấp phép lại và/hoặc bán bản sao của Phần mềm, đồng thời cho phép những người được cung cấp phần mềm có thể làm điều tương tự, với điều kiện sau đây:

Thông báo bản quyền trên và thông báo cho phép này phải được bao gồm trong tất cả các bản sao hoặc phần quan trọng của Phần mềm.

PHẦN MỀM ĐƯỢC CUNG CẤP "NGUYÊN TRẠNG", KHÔNG CÓ BẢO HÀNH DƯỚI BẤT KỲ HÌNH THỨC NÀO, DÙ LÀ RÕ RÀNG HAY NGỤ Ý, BAO GỒM NHƯNG KHÔNG GIỚI HẠN CÁC BẢO HÀNH VỀ KHẢ NĂNG BÁN ĐƯỢC, SỰ PHÙ HỢP VỚI MỤC ĐÍCH CỤ THỂ VÀ KHÔNG VI PHẠM. TRONG BẤT KỲ TRƯỜNG HỢP NÀO, TÁC GIẢ HOẶC CHỦ SỞ HỮU BẢN QUYỀN KHÔNG CHỊU TRÁCH NHIỆM VỀ BẤT KỲ YÊU CẦU, THIỆT HẠI HOẶC TRÁCH NHIỆM NÀO KHÁC, DÙ LÀ TRONG HỢP ĐỒNG, SAI LẦM DÂN SỰ HAY BẤT KỲ TRƯỜNG HỢP NÀO KHÁC, PHÁT SINH TỪ HOẶC CÓ LIÊN QUAN ĐẾN PHẦN MỀM HOẶC VIỆC SỬ DỤNG HOẶC CÁC GIAO DỊCH KHÁC TRONG PHẦN MỀM.
"""

import math
import os

from PIL import Image
from pyrogram import Client, raw
from pyrogram.file_id import FileId

# Kích thước tối đa của sticker Telegram
STICKER_DIMENSIONS = (512, 512)


async def resize_file_to_sticker_size(file_path: str) -> str:
    """Chỉnh kích thước ảnh về đúng kích thước sticker Telegram"""
    im = Image.open(file_path)
    if (im.width, im.height) < STICKER_DIMENSIONS:
        size1 = im.width
        size2 = im.height
        if im.width > im.height:
            scale = STICKER_DIMENSIONS[0] / size1
            size1new = STICKER_DIMENSIONS[0]
            size2new = size2 * scale
        else:
            scale = STICKER_DIMENSIONS[1] / size2
            size1new = size1 * scale
            size2new = STICKER_DIMENSIONS[1]
        size1new = math.floor(size1new)
        size2new = math.floor(size2new)
        sizenew = (size1new, size2new)
        im = im.resize(sizenew)
    else:
        im.thumbnail(STICKER_DIMENSIONS)
    try:
        os.remove(file_path)
        return f"{file_path}.png"
    finally:
        im.save(file_path)


async def upload_document(
    client: Client, file_path: str, chat_id: int
) -> raw.base.InputDocument:
    """Tải lên tài liệu (document) lên Telegram"""
    media = await client.send(
        raw.functions.messages.UploadMedia(
            peer=await client.resolve_peer(chat_id),
            media=raw.types.InputMediaUploadedDocument(
                mime_type=client.guess_mime_type(file_path) or "application/zip",
                file=await client.save_file(file_path),
                attributes=[
                    raw.types.DocumentAttributeFilename(
                        file_name=os.path.basename(file_path)
                    )
                ],
            ),
        )
    )
    return raw.types.InputDocument(
        id=media.document.id,
        access_hash=media.document.access_hash,
        file_reference=media.document.file_reference,
    )


async def get_document_from_file_id(
    file_id: str,
) -> raw.base.InputDocument:
    """Lấy thông tin tài liệu từ File ID"""
    decoded = FileId.decode(file_id)
    return raw.types.InputDocument(
        id=decoded.media_id,
        access_hash=decoded.access_hash,
        file_reference=decoded.file_reference,
    )
