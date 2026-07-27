from config import initialSize, eachSize

from tabulate import tabulate

local_pages = []  # 本地分页数据

def makePage(d):
    '''
    制作分页数据
    '''
    local_pages.clear()
    #if calcSize(d) > initialSize: # 总条数大于首屏数，使用本地分页
    if len(d) > initialSize:
        sublist = []
        for item in d:
            sublist.append(item)#问题有 2026.07.27改#
        #    for child in item["child"]:
        #        sublist.append(child)
        
        firstPageSize = min(len(sublist), initialSize) # 第一页的大小

        local_pages.append(sublist[0:firstPageSize]) # 取第一页的集合

        remain_size = len(sublist)-firstPageSize # 剩余条数

        group_count = int(remain_size / eachSize) # 计算分页数

        last_count = remain_size % eachSize # 取余，最后剩余多少条

        idx = 0
        for idx in range(group_count):
            start = firstPageSize + idx * eachSize
            end = start + eachSize
            local_pages.append(sublist[start:end]) # 新增页集合

        if last_count > 0:
            local_pages.append(sublist[-last_count:]) # 余数不为0，将作为最后一页集合
    else:#2026.07.24#
        local_pages.append(d)
    pass
                

'''def calcSize(d)->int:
    
    计算总条数
    
    size = 0
    for item in d:
        size += len(item["child"]) + 1
    return size'''

def printPage():
    '''
    打印页面
    '''
    idx = 0
    for p in local_pages:
        idx += 1
        print("page:{}".format(idx))
        '''for item in p:
            print(item)'''
        print(tabulate(p,headers="keys",tablefmt='grid'))#打印字典列表就是这么写的#2026.7.24#
        


'''data = [{"id":"1",
         "name":"parent_1",
         "child":[
             {"id":"1_1",
              "name":"RS234326348264",
              "parent_id":"1"
              },
             {"id":"1_2",
              "name":"RS234326348264",
              "parent_id":"1"
              },
             {"id":"1_3",
              "name":"RS234326348264",
              "parent_id":"1"
              }]},

        {"id":"2",
         "name":"parent_2",
         "child":[
              {"id":"2_1",
              "name":"RS234326348264",
              "parent_id":"2"
              }]}]'''

'''————————————————
版权声明：本文为CSDN博主「快乐星球没有乐」的原创文章，遵循CC 4.0 BY-SA版权协议，转载请附上原文出处链接及本声明。
原文链接：https://blog.csdn.net/m0_58477260/article/details/137918665
'''