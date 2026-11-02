from neo4jonth.OwlTreeNode import OwlTreeNode


class OwlTree:
    def __init__(self, root_value):
        self.root = OwlTreeNode(root_value, {}, -1, "", {})