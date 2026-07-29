#文心：#values = [d.get(key) for d in dict_list if key in d and condition(d.get(key))] #2026.07.29#
def ifvaluerepeat_dictlist(dict_list,key,value):
    all_values = [d.get(key) for d in dict_list]
    if value in all_values:
        return True