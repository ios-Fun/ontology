import neo4j
from neo4j import GraphDatabase

from neo4jonth.LabelGraph import LabelGraph
from mcp_neo4j_data_modeling.data_model import DataModel, Node, Property, Relationship

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "P@ssw0rd")

# ========== 连接 ==========
driver = GraphDatabase.driver(URI, auth=AUTH)

# 验证连接
driver.verify_connectivity()
print("连接成功")

def run_cypher(cypher: str, params: dict | None = None):
    """执行 Cypher，返回字典列表"""
    records = driver.execute_query(
        cypher,
        parameters_=params or {},
        result_transformer_=lambda r: r.data(),  # 直接转成 list[dict]
    )
    print(f" 返回 {len(records)} 条")
    return records

cypher = """
CALL db.labels() YIELD label RETURN label ORDER BY label
"""
results = run_cypher(cypher)

# 获取所有的label组合--set
labels_set = set()
# 获取所有的label组合--list
res_list = []
# labels组合的属性集合
pros_dic = {}

g = LabelGraph()

# 获取所有的label组合
for item in results:
    label = item["label"]
    params = {"label": label}
    cypher1 = f"""
    MATCH (n:`{label}`) RETURN distinct(labels(n)) LIMIT 50
    """
    results = run_cypher(cypher1)
    # print(results)
    for res in results:
        list_item = res["(labels(n))"]
        t = tuple(list_item)
        if t not in labels_set:
            # 如果包含Template，直接去掉
            if "Template" in list_item:
                continue
            labels_set.add(t)
            res_list.append(list_item)
            g.add_node(t)
            # 查询属性
            cypher_pros = f"""
            MATCH (n:`{label}`) RETURN DISTINCT apoc.meta.cypher.types(n) AS propTypeMap
            """
            results_pros = run_cypher(cypher_pros)
            pros_item_dic = {}
            for pros in results_pros:
                pros_propTypeMap = pros["propTypeMap"]
                for key, value in pros_propTypeMap.items():

                    if key not in pros_item_dic:
                        pros_item_dic[key] = value
            print(pros_item_dic)
            pros_dic[t] = pros_item_dic


print(res_list)
print(len(res_list))

# 定义图，结果放入图中

# 查询关联的关系、labels
for labels in res_list:
    cypher2 = f"""
    MATCH (n)
    WHERE labels(n) = {labels}
    MATCH (n)-[r]->(m)
    RETURN distinct(type(r)),labels(m)
    LIMIT 50
    """
    results = run_cypher(cypher2)
    source_t = tuple(labels)
    for res in results:
        relation = res["(type(r))"]
        if "REFERENCE_TEMPLATE" == relation:
            continue
        labels = res["labels(m)"]
        obj_t = tuple(labels)
        g.add_edge(source_t, obj_t, relation)


nodes = []
# to owl
# Node和属性对象
for labels in res_list:
    t = tuple(labels)
    labels_str = '_'.join(labels)

    # 属性
    properties = []
    label_pros_dic = pros_dic[t]
    for key,value in label_pros_dic.items():
        property_label = Property(name=key, type=value)
        # property.name = key
        # property.type = value
        properties.append(property_label)

    node = Node(
        label=labels_str,
        key_property=Property(
                name="id", type="STRING", description="Unique identifier"
            ),
        properties=properties,
    )
    nodes.append(node)

# 定义关系
relationships = g.print_graph()
data_model = DataModel(nodes=nodes, relationships=relationships)
turtle_str = data_model.to_owl_turtle_str()
with open('example.ttl', 'w', encoding="utf-8") as f:
    f.write(turtle_str)
driver.close()