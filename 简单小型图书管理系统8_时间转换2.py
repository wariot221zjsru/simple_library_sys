from tabulate import tabulate
import datetime#只引了一次，下面有些地方需要写datetime.datetime

from file_handler import load_data, save_data#
from config import * #引入所有配置的变量
from utils import *

import re
#2. 限定搜索特定键（推荐）#dpsk#
def find_indices_by_keys(data, pattern, keys=None, flags=0):#dpsk#
    """
    只搜索字典中指定的键（keys）对应的值
    keys: 字符串或字符串列表，若为 None 则搜索所有值
    """
    regex = re.compile(pattern, flags)
    indices = []
    if isinstance(keys, str):
        keys = [keys]
    for i, d in enumerate(data):
        # 确定要检查的键
        check_keys = keys if keys else d.keys()
        for key in check_keys:
            val = d.get(key)
            if isinstance(val, str) and regex.search(val):
                indices.append(i)
                break
    return indices


def return_borrowrcd_oprt(borrow):
    borrow["return_date"] = datetime.datetime.now()
    borrow["borrow_duration"]=borrow["return_date"]-borrow["borrow_date"]
    borrow["status"]="已归还"
    return borrow

#每次都需要重新定义borrows列表和borrow字典、book字典
borrows=[]
borrow={
"id": 0,
"isbn": "",
"bookname":"",#
"borrower": "",
"borrow_date": None,
"return_date": None,
"status": "",
"borrow_duration": ""
}
book={}#"ISBN","书名","作者","分类","库存数量","总量","可借数量","增加时间" 
#正常的初始化放在加载文件前面！！不然读不起来 #malam
books, borrows=load_data()
if books==-1 :
    #正文代码：
    
    books=[]#如果文件存在，那么[]也存在
    borrows=[{
    "id": 0,
    "isbn": "978-7-111-12345-6",
    "bookname":"",
    "borrower": "张三",
    "borrow_date": "2025-03-01",
    "return_date": None,
    "status": "borrowed",
    "borrow_duration": ""
    }]

elif borrows==[]:#若borrows为空，则初始化borrow字典，恢复默认有的值
    borrows=[{
    "id": 0,
    "isbn": "978-7-111-12345-6",
    "bookname":"",
    "borrower": "张三",
    "borrow_date": "2025-03-01",
    "return_date": None,
    "status": "borrowed",
    "borrow_duration": ""
    }]



while True:
    print('''
    ==============================
        图书管理系统 v1.0
    ==============================
    【1】图书管理
        1.1 新增图书
        1.2 查看全部图书
        1.3 查询图书
        1.4 修改图书信息
        1.5 删除图书
    【2】借阅管理
        2.1 借出图书
        2.2 归还图书
        2.3 查看借阅记录
    【3】数据统计
        3.1 图书总览
        3.2 逾期提醒
    【0】退出系统
    ==============================
    请输入选项编号: 
    ''')
    selection=float(input())
    if selection==1.1:
        bookname=str(input("书名："))
        writor=str(input("作者："))
        isbn=str(input("ISBN："))
        category=str(input("图书分类："))
        amount=int(input("库存数量："))
        
        add_time=str(datetime.datetime.now())

        book.update({"书名":bookname,"作者":writor,"ISBN":isbn,"分类":category,"库存数量":amount,"增加时间":add_time})
        books.append(book)

        print("添加一批图书成功！")

    elif selection==1.2:
        print(f"首屏展示条数:{initialSize}")
        print(f"剩余页展示条数:{eachSize}")
        makePage(books)
        printPage()
    elif selection==1.3:
        print("~~~~~多元素搜索~~~~~")
        bookname=str(input("书名："))
        writor=str(input("作者："))
        isbn=str(input("ISBN："))
        category=str(input("分类："))
        
        # 用于存储非空字段对应的索引集合
        sets_to_intersect = []
        '''
        bookname_ids=[]
        writor_ids=[]
        isbn_ids=[]
        category_ids=[]'''

        if bookname!="":
            bookname_ids=find_indices_by_keys(books,rf"{bookname}","书名")
            sets_to_intersect.append(set(bookname_ids))

        if writor!="":
            writor_ids=find_indices_by_keys(books,rf"{writor}","作者")
            sets_to_intersect.append(set(writor_ids))

        if isbn!="":
            isbn_ids=find_indices_by_keys(books,re.escape(isbn),"ISBN")#不做正则特殊符号功能#dpsk#2026.07.24#
            sets_to_intersect.append(set(isbn_ids))#


        if category!="":
            category_ids=find_indices_by_keys(books,rf"{category}","分类")
            sets_to_intersect.append(set(category_ids))
        
        #common_elements = set(bookname_ids) & set(writor_ids) & set(isbn_ids) & set(category_ids)#取交集
        
        #dpsk#
            # 根据是否存在筛选条件计算交集
        if not sets_to_intersect:
            # 没有任何筛选条件，返回所有记录的索引（例如范围0到len(books)-1）
            common_elements = set(range(len(books)))
        else:
            # 取所有非空字段集合的交集
            common_elements = set.intersection(*sets_to_intersect)#取交集

        # 提取这些索引对应的字典
        selected = [books[i] for i in common_elements]

        # 用 tabulate 打印
        print(tabulate(selected, headers="keys", tablefmt="grid"))
        #dpsk#

        # qyudai qiantu learnAI jichu fei_shijigongzuo_changjing_XianxueErfeixiaolv
        #jishutailaod php gongsi fazhanqianjingBuda
    elif selection == 0:
        save_data(books, borrows)
        print("确定退出？(Y/N)")
        if input().upper()!="Y":#
            continue
        print("感谢使用图书系统，再见")
        import sys
        sys.exit()
    elif selection==1.4:
        print ("请输入要修改的图书的ISBN：")
        isbn = input()
        for book in books:
            if book["ISBN"] == isbn:
                print("请输入要修改的图书信息：")
                bookname= input("书名：")
                writor= input("作者：")
                
                category= input("分类：")
                amount=book["库存数量"] = input("库存数量：")
        
           # 非空即改
            if bookname!="":
                book["书名"]=bookname
            if writor!="":
                book["作者"] = writor
            if category!="":
                book["分类"] = category
            if amount!="":
                book["库存数量"] = int(amount)

            #Kanzhemechangshijian ? Xuezhememan ? Video ketiaoguo

            print("修改成功！")

    if selection==1.5:
        isbn = input("请输入要删除的图书的ISBN：")
        for book in books:
            if book["ISBN"] == isbn:
                #remove 删除第一个与指定值相同的元素
                books.remove(book)
                print("删除成功！")
                break
        else:
            print("未找到该图书！")
    


    if selection==2.1:
        print("请输入书名或ISBN:")
        bookname_or_isbn = input()

        for book in books: #自 补
            if book["书名"] == bookname_or_isbn or book["ISBN"] == bookname_or_isbn:
                if book["库存数量"] > 0:
                    book["库存数量"] -= 1
                    
                    borrow["isbn"] = book["ISBN"]
                    borrow["bookname"] = book["书名"]
                    borrow["borrower"] = input("借阅人：")
                    borrow["borrow_date"] =datetime.datetime.now()
                    borrow["status"]="已借出"
                    borrows.append(borrow)##添加借阅记录
                    print("借出成功！")
                    
                else:
                    print("库存不足！")
                break
        else:
            print("未找到该图书！")
    if selection==2.2:
        name=input("请输入你的姓名：")
        print("请输入要归还的图书书名或ISBN：")
        isbn = input()

        borrownum=0
        personal_borrows=[]
        for i in range(len(borrows)): 
            if name==borrows[i]["borrower"]:
                borrownum+=1
                personal_borrows.append(i)#还是用索引更好，因为要先看有几本书，如果多的话再输书名再判断，索引值更好判断
                #找到个人借书借书号，并判断是否有多本借书#2026.07.24#


        if borrownum==1:
            bookname_or_isbn=borrows[personal_borrows[0]]["isbn"] #借书列表[借书序号][结束字典中的isbn键]
                                                                  #其中借书序号来自personal_borrows列表
            borrows[personal_borrows[0]]=return_borrowrcd_oprt(borrows[personal_borrows[0]])# borrows[这个人是哪一条记录（用索引编号表示）]
        #malam#之前的问题是缺乏返回值引起的
        else:
            bookname_or_isbn=input("请输入要归还的图书书名或ISBN：")#


        for book in books: #自 补
            #找到是哪个书
            if book["书名"] == bookname_or_isbn or book["ISBN"] == bookname_or_isbn:
                book["库存数量"] += 1 #库存数量
        for borrow_id in personal_borrows:#如果有多本书，用isbn或书名结合 个人借书记录序号 找到是哪个记录
            if borrows[borrow_id]["isbn"] ==bookname_or_isbn or borrows[borrow_id]["bookname"]==bookname_or_isbn: #借书字典表[借书记录号][ISBN]
                borrows[borrow_id]=return_borrowrcd_oprt(borrows[borrow_id])#修改记录

        print("成功归还图书！")

    if selection==2.3:
        print('''借还书记录查询
              1：查询全部
              2:查询未归还书籍
              3.查询已归还书籍''')
        borrow_selection=int(input("请选择查询方式："))

        if borrow_selection==1:
            print(tabulate(borrows,headers="keys",tablefmt='grid'))
        elif borrow_selection==2:
            not_return=[]
            for borrow in borrows:
                if borrow["status"]=="已借出":
                    not_return.append(borrow)
            print(tabulate(not_return,headers="keys",tablefmt='grid'))
            

        elif borrow_selection==3:
            returned=[]
            for borrow in borrows:
                if borrow["status"]=="已归还":#找出已归还书籍，存入列表，直接打印
                    returned.append(borrow)
            print(tabulate(returned,headers="keys",tablefmt='grid'))

    if selection==3.1:
        print("馆藏图书种数：",len(books))#不能用sum

        print("馆藏图书总册数：",sum(book["库存数量"] for book in books),"册")

        category_set=set(book["分类"] for book in books)

        #keys_dict_with_default = dict.fromkeys(keys, 'default_value')

        # 使用字典推导式创建字典，所有值设为None
        category_dict = {key: [0,0] for key in category_set}
        
        
        #计算未借出和已借出的分类总册数
        for book in books:
            category_dict[book["分类"]][0] += book["库存数量"] #分类字典[遍历到的书的分类][第一个值]+=这种书的数量
            category_dict[book["分类"]][1] +=1
        for borrow in borrows:
            if borrow["status"]=="已借出":
                for book in books:
                    if book["ISBN"]==borrow["isbn"]:
                        category_dict[book["分类"]][0] += 1
                        break#只要查到书号就行了
        
        for key,value in category_dict.items():
            print(f"{key}类：总册数：{value[0]}册，图书种数：{value[1]}")
    
        #示例：## 使用filter函数筛选具有特定'status'为'active'的字典
        #active_entries = list(filter(lambda x: x.get('status') == 'active', data))
        borrowed_books=list(filter(lambda x: x.get('status') == '已借出', borrows))#
        #filter 对象是惰性求值的，不存储所有元素，因此不知道长度。
        print("已借出的图书册数为:",len(borrowed_books),"（册）")

    if selection==3.2:
        overdue=filter(lambda x: x.get('status') == '已借出' and  datetime.datetime.now()>x.get('borrow_date') +datetime.timedelta(days=30), borrows)
        print(tabulate(overdue,headers="keys",tablefmt='grid'))
        

    print("按回车键继续...")
    input()   # 等待用户按回车


