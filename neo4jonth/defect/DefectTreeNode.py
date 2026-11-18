
class DefectTreeNode:
    def __init__(self, name, valueDic, type, status):
        self.name = name
        self.valueDic = valueDic
        # 0-运算符，1--逻辑特征
        self.type = type
        self.children = []  # 存放子节点列表
        self.status = status
        self.parent = None

    def add_child(self, child_node):
        """添加子节点"""
        self.children.append(child_node)

    def set_parent(self, parent):
        self.parent = parent