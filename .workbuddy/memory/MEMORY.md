# 项目长期记忆

## 项目概述
- **名称**：简易图书管理系统（BookManager）
- **位置**：E:\杭电培训-AI应用\考试\第二周-改\加QT
- **用途**：杭电培训 AI 应用考试第二周作业
- **技术栈**：Python 3.x + PyQt5（GUI）/ 纯 CLI（原版）

## 文件结构
- `简单小型图书管理系统8_时间转换2.py` —— 原 CLI 主程序（while 循环菜单）
- `config.py` —— 配置：DATA_FILE, initialSize=2, eachSize=5
- `file_handler.py` —— 数据持久化：load_data/save_data + datetime 自定义 JSON 编解码
- `utils.py` —— 分页：makePage/printPage（使用 tabulate 第三方库）
- `library_data.json` —— 数据存储（books + borrows）
- `library_gui.py` —— PyQt5 图形界面版（2026-07-27 新增）

## 运行环境
- **必须使用系统 Python**：`C:\Python312\python.exe`（已装 PyQt5 + tabulate）
- 管理版 Python 3.13.12 未安装 PyQt5/tabulate，不可用于本项目
- 运行 GUI：`C:\Python312\python.exe library_gui.py`
- 运行 CLI：`C:\Python312\python.exe 简单小型图书管理系统8_时间转换2.py`

## 数据结构
- Book 字典键：书名, 作者, ISBN, 分类, 库存数量, 增加时间
- Borrow 字典键：id, isbn, bookname, borrower, borrow_date, return_date, status, borrow_duration
- status 有两种写法："已借出"/"borrowed"（未归还）、"已归还"（已归还）

## 注意事项
- 原 CLI 有 dict 引用共享 bug（book={} 在循环外定义），导致重复数据
- 原 CLI 修改功能有缩进 bug（if 判断在 for 循环外）
- GUI 版已修复这些问题，但不改动原 CLI 代码
