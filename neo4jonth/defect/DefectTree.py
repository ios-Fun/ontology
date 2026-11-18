from neo4jonth.defect.DefectTreeNode import DefectTreeNode


class DefectTree:
    def __init__(self, root_value):
        self.root = DefectTreeNode("root", {}, root_value, status="")