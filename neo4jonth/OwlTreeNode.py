class OwlTreeNode:
    def __init__(self, name,value,type, pName, propTypeMap):
        self.name = name
        self.value = value
        self.type = type
        self.children = []  # 存放子节点列表
        self.pName = pName  # 父节点的名字
        self.propTypeMap = propTypeMap  # 属性类型字典

    def add_child(self, child_node):
        """添加子节点"""
        self.children.append(child_node)

    def set_pName(self, pName):
        self.pName = pName

    def remove_child(self, child_node):
        """移除子节点"""
        self.children = [c for c in self.children if c != child_node]