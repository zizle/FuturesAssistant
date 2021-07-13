# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2021-03-17 14:43
# @Author: zizle
# 项目工具箱


class ListAndTree(object):  # 将扁平化列表和树的转换
    def __init__(self):
        super(ListAndTree, self).__init__()

    def list2tree(self, data: list, pid: int):
        return [dict(menu, **{'children': self.list2tree(data, menu['menu_id'])}) for menu in
                [m for m in data if m['parent_id'] == pid]]

    def tree2list(self, data: dict):
        pass


if __name__ == '__main__':
    menus = [{'menu_id': 1, 'name': 'xx', 'parent_id': 0}, {'menu_id': 2, 'name': 'xx-1', 'parent_id': 1},
             {'menu_id': 3, 'name': '主2', 'parent_id': 0}, {'menu_id': 4, 'name': '主2-1', 'parent_id': 3},
             {'menu_id': 5, 'name': 'xx-2', 'parent_id': 1},
             {'menu_id': 6, 'name': 'xx--1-1', 'parent_id': 2}]
    obj = ListAndTree()
    print(obj.list2tree(menus, 0))
