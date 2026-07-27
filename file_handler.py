import datetime
#dpsk#
import json
import os

from config import DATA_FILE

##日期转换#dpsk#2026.07.24#################

#timedelta转换成秒 #malam #malam#

class DateTimeEncoder(json.JSONEncoder):
    """自定义 JSON 编码器，支持 datetime 和 timedelta"""
    def default(self, obj):
        if isinstance(obj, datetime.datetime):#datetime.
            return obj.isoformat()
        if isinstance(obj, datetime.timedelta):#datetime.
            # 将 timedelta 存储为特殊结构的字典
            return {
                "__type__": "timedelta",
                "seconds": obj.total_seconds()
            }
        # 其他类型交给父类处理（可能抛出异常）
        return super().default(obj)

def datetime_decoder(dct):
    """
    自定义 JSON 解码器（object_hook），用于还原 datetime 和 timedelta。
    该函数会被递归调用到每个字典。
    """
    # 检查是否是我们存储的 timedelta 结构
    if dct.get("__type__") == "timedelta":
        seconds = dct.get("seconds", 0)
        return datetime.timedelta(seconds=seconds)#datetime.

    # 否则尝试将字典中的字符串值解析为 datetime
    for key, value in dct.items():
        if isinstance(value, str):
            try:
                # 尝试解析 ISO 格式的日期时间字符串
                dct[key] = datetime.datetime.fromisoformat(value)#datetime.
            except ValueError:
                pass   # 不是日期格式，保持原样
    return dct
#####################



def load_data():##dpsk#
    """
    从 JSON 文件加载 books 和 borrows 列表。
    如果文件不存在或损坏，返回空列表。
    """
    if not os.path.exists(DATA_FILE):
        return -1,-1 # [], []   # 首次运行，返回空列表

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f, object_hook=datetime_decoder)#时间转换 函数调用
        books = data.get("books", [])
        borrows = data.get("borrows", [])
        return books, borrows
    except (json.JSONDecodeError, KeyError, IOError):
        # 文件损坏或格式不对，重置为空
        print("数据文件损坏，将重新初始化。")
        return -1,-1 #2026.07.24#[], []
'''存进 JSON 的是 datetime 对象的 isoformat() 字符串（不是时间对象），类似 "2026-07-24T15:30:00"。

这个字符串包含了日期、时间和时区信息（如果有的话），可以被任何语言或库解析。

读取时，代码通过 datetime.fromisoformat() 将其转回 Python 的 datetime 对象，所以你在程序中操作时仍然是 datetime 类型，完全透明。'''
def save_data(books, borrows):
    """
    将 books 和 borrows 保存到 JSON 文件。
    """
    data = {
        "books": books,
        "borrows": borrows
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4, cls=DateTimeEncoder)#时间转换