class OwlTreeNode:
    def __init__(self, name,value,type, pName, propTypeMap):
        self.name = name
        self.value = value
        self.type = type
        self.children = []  # 存放子节点列表
        self.pName = pName  # 父节点的名字
        self.propTypeMap = propTypeMap  # 属性类型字典
        self.parents = set() # 父节点集合
        self.is_referenced = False # 标记是否被引用
        self.partOfTo = []

    def add_child(self, child_node):
        """添加子节点"""
        self.children.append(child_node)

    def add_parent(self, parent_node):
        """添加子节点"""
        self.parents.add(parent_node)

    def set_pName(self, pName):
        self.pName = pName

    def add_partOf(self, partOfNode):
        self.partOfTo.append(partOfNode)

    def remove_child(self, child_node):
        """移除子节点"""
        self.children = [c for c in self.children if c != child_node]