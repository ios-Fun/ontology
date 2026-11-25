
class DefectTreeNode:
    def __init__(self, name, valueDic, type, status):
        # 运算符--对应运算符名字，逻辑特征--对应编码
        self.name = name
        # 属性字典
        self.valueDic = valueDic
        # 0-运算符，1--逻辑特征
        self.type = type
        self.children = []  # 存放子节点列表
        # 如偏大、快速上升
        self.status = status
        self.parent = None
        # 故障模式index
        self.defect_index = 0
        # 权重
        self.weight = None

    def add_child(self, child_node):
        """添加子节点"""
        self.children.append(child_node)

    def set_parent(self, parent):
        self.parent = parent

    def set_defect_index(self, index):
        self.defect_index = index

    def set_weight(self, weight):
        self.weight = weight