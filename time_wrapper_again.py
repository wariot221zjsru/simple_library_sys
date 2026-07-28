import time
import sys
from PyQt5.QtWidgets import QApplication, QMessageBox, QMainWindow

APP_NAME = "MyApp"
APP_VERSION = "1.0"

# 假设你已有 logger
# import logging
# logger = logging.getLogger(__name__)


def format_dhms(total_seconds):
    """将小数秒转为 天时分秒（保留完整精度）"""
    sign = -1 if total_seconds < 0 else 1
    total_seconds = abs(total_seconds)
    days, rem = divmod(total_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{sign * int(days)}天{int(hours)}小时{int(minutes)}分{seconds:.9f}秒"#


def timer_with_final_popup(func):
    """装饰器：记录程序运行总时长，并在程序退出时弹窗显示"""
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()

        try:
            # 执行主函数，期望返回 (app, exit_code)
            # 必须保留 app 引用，否则 QApplication 被 GC 后 QMessageBox 无法创建
            app, exit_code = func(*args, **kwargs)
        except Exception as e:
            # 如果 main 内部有致命异常（连 app 都没生成），直接退出
            print(f"Critical error: {e}")
            sys.exit(1)

        end_time = time.perf_counter()
        elapsed = end_time - start_time
        time_str = format_dhms(elapsed)

        # 🟢 关键操作：在主循环已停止的情况下，弹出新窗口
        # QMessageBox.exec_() 会启动本地事件循环，所以依然能正常显示
        msg_box = QMessageBox()#####这边括号里删掉了app
        #原有问题：QMessageBox 的构造函数的第一个参数要求是 QWidget 类型（或 None），而 QApplication 并不是 QWidget 的子类，因此引发了类型错误。

        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("运行统计")
        msg_box.setText(f"程序已运行：\n{time_str}")
        msg_box.exec_()  # 阻塞，等待用户点击

        # 用户点击后，正式退出进程
        sys.exit(exit_code)

    return wrapper