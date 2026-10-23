from typing import Dict, Set, List, Tuple
from mcp_neo4j_data_modeling.data_model import DataModel, Node, Property, Relationship

# 标签组合，如 ("测点", "Entity", "Instance", "开关量")
LabelGroup = Tuple[str, ...]
RelType = str

class LabelGraph:
    def __init__(self):
        # 顶点集合：存放所有唯一标签组合
        self.nodes: Set[LabelGroup] = set()
        # 邻接表： key=起点标签组, value={(终点标签组, 关系类型)}
        self.adj: Dict[LabelGroup, Set[Tuple[LabelGroup, RelType]]] = {}

    def add_node(self, labels: List[str] | Tuple[str, ...]):
        """添加一个标签组合节点，自动去重"""
        t = tuple(labels)
        self.nodes.add(t)
        if t not in self.adj:
            self.adj[t] = set()

    def add_edge(self, src_labels: List[str] | Tuple[str, ...],
                 dst_labels: List[str] | Tuple[str, ...],
                 rel_type: str):
        """添加一条关系，src -> dst，关系类型rel_type，自动去重"""
        s = tuple(src_labels)
        d = tuple(dst_labels)
        # 两端节点自动注册
        self.add_node(s)
        self.add_node(d)
        self.adj[s].add((d, rel_type))

    def get_all_nodes(self) -> List[List[str]]:
        """返回所有节点，转成list格式方便打印"""
        return [list(n) for n in self.nodes]

    def get_edges(self) -> List[dict]:
        """返回所有边，结构化输出"""
        edges = []
        for src, targets in self.adj.items():
            for dst, rtype in targets:
                edges.append({
                    "src_labels": list(src),
                    "rel_type": rtype,
                    "dst_labels": list(dst)
                })
        return edges

    def print_graph(self)->List[Relationship]:
        relationships = []

        print("===== 标签组节点 =====")
        for n in self.get_all_nodes():
            print(n)
        print("\n===== 关系边 =====")
        for e in self.get_edges():
            src_labels = e["src_labels"]
            dst_labels = e["dst_labels"]
            if "Template" in src_labels:
                continue
            if "Template" in dst_labels:
                continue

            src_labels_str = '_'.join(src_labels)
            dst_labels_str = '_'.join(dst_labels)
            print(f"{src_labels_str}  -[{e['rel_type']}]->  {dst_labels_str}")

            relationship = Relationship(
                type=e['rel_type'],
                start_node_label=src_labels_str,
                end_node_label=dst_labels_str,
                properties=[]
            )
            relationships.append(relationship)
        return relationships

# # ---------------- 测试示例 ----------------
# if __name__ == "__main__":
#     g = LabelGraph()
#     # 添加节点
#     g.add_node(["Logic", "Property"])
#     g.add_node(["Entity", "Property"])
#     g.add_node(["测点", "Entity", "Instance", "开关量"])
#
#     # 添加关系
#     g.add_edge(["Logic", "Property"], ["Entity", "Property"], "hasA")
#     g.add_edge(["测点", "Entity", "Instance", "开关量"], ["Entity", "Property"], "belong")
#
#     g.print_graph()
