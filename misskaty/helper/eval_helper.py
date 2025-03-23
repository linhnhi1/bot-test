import ast
import os
import traceback
from typing import List, Optional

# Chúng ta không thay đổi biến cục bộ (locals), điều này giúp giữ nguyên tin nhắn cho hàm do người dùng cung cấp
async def meval(code, globs, **kwargs):
    # Hàm này được phát hành dưới dạng mã nguồn mở. Bạn có thể sử dụng nó tự do (nhưng tôi sẽ rất vui nếu được ghi nhận công lao)
    # Lưu ý: Đừng đặt biến global ở đây vì chúng có thể bị mất.
    # Tránh làm lộn xộn không gian cục bộ
    locs = {}
    # Sao chép lại biến toàn cục để sử dụng sau
    globs = globs.copy()
    # Lưu các biến hệ thống như __name__ và __package__ vào tham số để đảm bảo import tương đối hoạt động
    global_args = "_globs"
    while global_args in globs.keys():
        # Đảm bảo không có sự trùng lặp tên, cứ tiếp tục thêm dấu gạch dưới (_)
        global_args = f"_{global_args}"
    kwargs[global_args] = {}
    for glob in ["__name__", "__package__"]:
        # Sao chép dữ liệu vào tham số để gửi
        kwargs[global_args][glob] = globs[glob]

    root = ast.parse(code, "exec")
    code = root.body

    ret_name = "_ret"
    ok = False
    while True:
        if ret_name in globs.keys():
            ret_name = f"_{ret_name}"
            continue
        for node in ast.walk(root):
            if isinstance(node, ast.Name) and node.id == ret_name:
                ret_name = f"_{ret_name}"
                break
            ok = True
        if ok:
            break

    if not code:
        return None

    # Kiểm tra nếu mã không có lệnh `return`, thay vào đó hãy in ra giá trị cuối cùng
    if not any(isinstance(node, ast.Return) for node in code):
        for i in range(len(code)):
            if isinstance(code[i], ast.Expr) and (
                i == len(code) - 1 or not isinstance(code[i].value, ast.Call)
            ):
                code[i] = ast.copy_location(
                    ast.Expr(
                        ast.Call(
                            func=ast.Attribute(
                                value=ast.Name(id=ret_name, ctx=ast.Load()),
                                attr="append",
                                ctx=ast.Load(),
                            ),
                            args=[code[i].value],
                            keywords=[],
                        )
                    ),
                    code[-1],
                )
    else:
        for node in code:
            if isinstance(node, ast.Return):
                node.value = ast.List(elts=[node.value], ctx=ast.Load())

    code.append(
        ast.copy_location(
            ast.Return(value=ast.Name(id=ret_name, ctx=ast.Load())), code[-1]
        )
    )

    # Cập nhật biến toàn cục trong hàm
    glob_copy = ast.Expr(
        ast.Call(
            func=ast.Attribute(
                value=ast.Call(
                    func=ast.Name(id="globals", ctx=ast.Load()), args=[], keywords=[]
                ),
                attr="update",
                ctx=ast.Load(),
            ),
            args=[],
            keywords=[
                ast.keyword(arg=None, value=ast.Name(id=global_args, ctx=ast.Load()))
            ],
        )
    )
    ast.fix_missing_locations(glob_copy)
    code.insert(0, glob_copy)

    # Khởi tạo biến lưu trữ kết quả trả về
    ret_decl = ast.Assign(
        targets=[ast.Name(id=ret_name, ctx=ast.Store())],
        value=ast.List(elts=[], ctx=ast.Load()),
    )
    ast.fix_missing_locations(ret_decl)
    code.insert(1, ret_decl)

    args = []
    for a in list(map(lambda x: ast.arg(x, None), kwargs.keys())):
        ast.fix_missing_locations(a)
        args += [a]
    args = ast.arguments(
        args=[],
        vararg=None,
        kwonlyargs=args,
        kwarg=None,
        defaults=[],
        kw_defaults=[None for _ in range(len(args))],
    )
    args.posonlyargs = []

    # Định nghĩa một hàm bất đồng bộ tạm thời để thực thi mã
    fun = ast.AsyncFunctionDef(
        name="tmp", args=args, body=code, decorator_list=[], returns=None
    )
    ast.fix_missing_locations(fun)
    mod = ast.parse("")
    mod.body = [fun]
    comp = compile(mod, "<string>", "exec")

    exec(comp, {}, locs)

    r = await locs["tmp"](**kwargs)
    for i in range(len(r)):
        if hasattr(r[i], "__await__"):
            r[i] = await r[i]  # Giải pháp thay thế cho Python 3.5
    i = 0
    while i < len(r) - 1:
        if r[i] is None:
            del r[i]
        else:
            i += 1
    if len(r) == 1:
        [r] = r
    elif not r:
        r = None
    return r


def format_exception(
    exp: BaseException, tb: Optional[List[traceback.FrameSummary]] = None
) -> str:
    """Định dạng lỗi dưới dạng chuỗi, giống như cách trình thông dịch Python hiển thị."""

    if tb is None:
        tb = traceback.extract_tb(exp.__traceback__)

    # Thay thế đường dẫn tuyệt đối bằng đường dẫn tương đối
    cwd = os.getcwd()
    for frame in tb:
        if cwd in frame.filename:
            frame.filename = os.path.relpath(frame.filename)

    stack = "".join(traceback.format_list(tb))
    msg = str(exp)
    if msg:
        msg = f": {msg}"

    return f"Traceback (most recent call last):\n{stack}{type(exp).__name__}{msg}"
