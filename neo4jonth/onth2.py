from collections import deque

from exceptiongroup import catch
from neo4j import GraphDatabase

from neo4jonth.OwlTree import OwlTree
from neo4jonth.OwlTreeNode import OwlTreeNode
from rdflib import OWL, RDF, RDFS, XSD, Graph, Namespace, URIRef, Literal, BNode
from datetime import datetime, timezone, timedelta
from rdflib.extras.infixowl import Class, Property, Restriction
import pandas as pd

from neo4jonth.defect.defectGraphToLan import parseDefectById

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "P@ssw0rd")

# ========== 连接 ==========
driver = GraphDatabase.driver(URI, auth=AUTH)

# 验证连接
driver.verify_connectivity()

def run_cypher(cypher: str, params: dict | None = None):
    """执行 Cypher，返回字典列表"""
    records = driver.execute_query(
        cypher,
        parameters_=params or {},
        result_transformer_=lambda r: r.data(),  # 直接转成 list[dict]
    )
    # print(f" 返回 {len(records)} 条")
    return records

# 定义二维数组
full_type_list = ['电厂', '机组', '系统', '子系统', '设备', '部件', '特征', '测点','故障模式']
type_list = ['电厂', '机组', '系统', '子系统', '设备', '部件', '特征','', '故障模式']

# full_type_list = ['电厂', '机组', '系统', '子系统', '设备', '部件', '特征', '测点']
# type_list = ['电厂', '机组', '系统', '子系统', '设备', '部件', '特征']

# 二维数组，一维是full_type_list，二维是模板，模型，实例
entity_arr = []
for item in type_list:
    item_list = []
    entity_arr.append(item_list)
    for j in range(3):
        item_list.append({})

# 树的根节点
tree = OwlTree("root")

def getIndex(labels):
    for index, item in enumerate(full_type_list):
        if item in labels:
            return index
    # label_str = ''
    # for item in labels:
    #     if item != "Entity" and item != "Model" and item != "Instance":
    #         label_str = item
    #         break
    # for index,item in enumerate(full_type_list):
    #     if label_str == item:
    #         return index
    return -1
# 处理child关系
def deal_PartOf(index):
    type = type_list[index]
    if len(type) == 0:
        return ""
    entity_type_str = ''
    if type == "故障模式":
        entity_type_str = 'Logic'
    else:
        entity_type_str = 'Entity'
    print(f"type1:{type}")
    # 模型
    t_cyper1 = f"MATCH (m:{entity_type_str}:Model)-[:CHILD_NODE]->(n:`{type}`:Entity:Model) RETURN m,n, labels(m) as labels_m, labels(n) as labels_n"
    if type == "故障模式":
        t_cyper1 = f"MATCH (m:`{type}`:{entity_type_str}:Model)-[:CHILD_NODE]->(n:Entity:Model) RETURN m,n, labels(m) as labels_m, labels(n) as labels_n"

    t_results1 = run_cypher(t_cyper1)
    deal_name_dic1 = entity_arr[index][1]
    print(f"Model count:{len(t_results1)}")
    for item in t_results1:
        from_node = item['m']
        to_node = item['n']
        from_node_labels = item['labels_m']
        to_node_labels = item['labels_n']
        # to_node_key = f"{to_node['名称']}_{to_node['编码']}"
        to_node_key = ""
        if '编码' in to_node:
            to_node_key = to_node['编码']
        else:
            print(f"error2-12: {to_node['名称']}")
            to_node_key = to_node['名称']
            # continue

        to_node_key = to_node_key.replace(" ", "")
        to_node_value = None
        if type == "故障模式":
            to_node_index = getIndex(to_node_labels)
            to_node_value = entity_arr[to_node_index][1][to_node_key]
        else:
            to_node_value = deal_name_dic1[to_node_key]
        if to_node_value is None:
            print(f"error1: {to_node_key}")

        from_node_key = ""
        if '编码' in from_node:
            from_node_key = from_node['编码']
        else:
            print(f"error2-13: {from_node['名称']}")
            from_node_key = from_node['名称']
            # continue
        from_node_key = from_node_key.replace(" ", "")
        from_node_index = getIndex(from_node_labels)
        if from_node_index == -1:
            continue
        from_type_dic = entity_arr[from_node_index][1]
        from_node_value = from_type_dic[from_node_key]
        if from_node_value is None:
            print(f"error: {from_node_key}")
        from_node_value.add_partOf(to_node_value)

    # 实例与实例之间的关系
    t_cyper2 = f"MATCH (m:{entity_type_str}:Instance)-[:CHILD_NODE]->(n:`{type}`:Entity:Instance) RETURN m,n, labels(m) as labels_m, apoc.meta.cypher.types(m) AS propTypeMap, id(m) as id_m, labels(n) as labels_n"
    if type == "故障模式":
        t_cyper2 = f"MATCH (m:`{type}`:{entity_type_str}:Instance)-[:CHILD_NODE]->(n:Entity:Instance) RETURN m,n, labels(m) as labels_m, apoc.meta.cypher.types(m) AS propTypeMap, id(m) as id_m, labels(n) as labels_n"
    t_results2 = run_cypher(t_cyper2)
    print(f"Instance count:{len(t_results2)}")
    deal_name_dic2 = entity_arr[index][2]
    for item in t_results2:
        from_node = item['m']
        to_node = item['n']
        from_node_labels = item['labels_m']
        to_node_labels = item['labels_n']
        # to_node_key = f"{to_node['名称']}_{to_node['编码']}"
        to_node_key = ""
        if '编码' in to_node:
            to_node_key = to_node['编码']
        else:
            print(f"error2-14: {to_node['名称']}")
            to_node_key = to_node['名称']
            # continue

        to_node_key = to_node_key.replace(" ", "")

        to_node_value = None
        if type == "故障模式":
            to_node_index = getIndex(to_node_labels)
            to_node_value = entity_arr[to_node_index][2][to_node_key]
        else:
            to_node_value = deal_name_dic2[to_node_key]
        if to_node_value is None:
            print(f"error1: {to_node_key}")

        from_node_key = ""
        if '编码' in from_node:
            from_node_key = from_node['编码']
        else:
            print(f"error2-15: {from_node['名称']}")
            from_node_key = from_node['名称']
            # continue
        from_node_key = from_node_key.replace(" ", "")
        from_node_index = getIndex(from_node_labels)
        if from_node_index == -1:
            continue
        if from_node_index == 7:
            # 测点, 挂在特征的model下
            pName = to_node_value.pName
            # 特征实例的父节点
            p_Node = None
            if pName not in deal_name_dic1:
                if pName not in entity_arr[index][0]:
                    print(f"error p_Node: {from_node_key}")
                    continue
                p_Node = entity_arr[index][0][pName]
            else:
                p_Node = deal_name_dic1[pName]

            propTypeMap = item['propTypeMap']
            from_node_id = item['id_m']
            propTypeMap['id'] = 'STRING'
            from_node['id'] = from_node_id
            treeNode = OwlTreeNode(from_node_key, from_node, 2, pName=pName, propTypeMap=propTypeMap)
            deal_name_dic2[from_node_key] = treeNode
            p_Node.add_child(treeNode)
            from_node_index = from_node_index - 1

        from_type_dic = entity_arr[from_node_index][2]
        if from_node_key not in from_type_dic:
            print(f"error2-16: {from_node_key}")
        from_node_value = from_type_dic[from_node_key]
        if from_node_value is None:
            print(f"error: {from_node_key}")
        from_node_value.add_partOf(to_node_value)

# 获取每个class和实例，以及之间的引用关系（对应owl的子类）
def deal_subClass_type(index):
    type = type_list[index]
    if len(type) == 0:
        return ""
    print(f"type:{type}")
    entity_type_str = ''
    if type == "故障模式":
        entity_type_str = 'Logic'
    else:
        entity_type_str = 'Entity'
    # global powerplant_OwlTree
    # 模板
    cyper0 = f"MATCH (m:`{type}`:{entity_type_str}:Template) return m, apoc.meta.cypher.types(m) AS propTypeMap"
    results0 = run_cypher(cyper0)

    # 顶层节点，如电厂
    topNode = OwlTreeNode(type, {}, -1, pName="", propTypeMap={})
    tree.root.add_child(topNode)

    deal_name_dic0 = entity_arr[index][0]
    # 处理重名
    for item in results0:
        value = item['m']
        propTypeMap = item['propTypeMap']
        format_name = value['编码'].replace(" ", "")
        if format_name not in deal_name_dic0:
            treeNode = OwlTreeNode(format_name, value, 0, pName=type, propTypeMap=propTypeMap)
            deal_name_dic0[format_name] = treeNode
            topNode.add_child(treeNode)
    print(f"Template count:{len(deal_name_dic0)}")
    # 模型 -先所有的
    cyper1 = f"MATCH (m:`{type}`:{entity_type_str}:Model) return m, apoc.meta.cypher.types(m) AS propTypeMap"
    results1 = run_cypher(cyper1)

    # model所有的，的字典，key：名称， value： 节点
    deal_name_dic1 = entity_arr[index][1]
    all_name_set1 = set()

    for item in results1:
        value = item['m']
        propTypeMap = item['propTypeMap']
        format_name = ""
        if '编码' in value:
            format_name = value['编码']
        else:
            print(f"error1—2: {value['名称']}")
            format_name = value['名称']
        format_name = format_name.replace(" ", "")
        if format_name not in deal_name_dic0:
            if type == "故障模式":
                df = pd.DataFrame(columns=["id", "名称", "描述"])
                defect_content = parseDefectById(0, format_name, value['名称'], df)
                # defect_content = 'abc'
                value['modelFaultLogicDescription'] = defect_content
                propTypeMap['modelFaultLogicDescription'] = 'STRING'

            treeNode = OwlTreeNode(format_name, value, 1, pName="", propTypeMap=propTypeMap)
            deal_name_dic1[format_name] = treeNode
            all_name_set1.add(format_name)
            if format_name == 'MAA01Z4QM311TXB01':
                treeNode.set_pName(type)
                topNode.add_child(treeNode)
    print(f"Model count:{len(deal_name_dic1)}")

    # model 与 模板之间的层级关系
    t_cyper1 = f"MATCH (m:`{type}`:{entity_type_str}:Model)-[:REFERENCE_TEMPLATE]->(n:`{type}`:{entity_type_str}:Template) RETURN m,n"
    t_results1 = run_cypher(t_cyper1)

    for item in t_results1:
        from_node = item['m']
        to_node = item['n']
        # to_node_key = f"{to_node['名称']}_{to_node['编码']}"
        to_node_key = ""
        if '编码' in to_node:
            to_node_key = to_node['编码']
        else:
            print(f"error2-2: {to_node['名称']}")
            # continue

        to_node_key = to_node_key.replace(" ", "")
        to_node_value = deal_name_dic0[to_node_key]
        if to_node_value is None:
            print(f"error1: {to_node_key}")

        from_node_key = ""
        if '编码' in from_node:
            from_node_key = from_node['编码']
        else:
            print(f"error2-3: {from_node['名称']}")
            from_node_key = from_node['名称']
        from_node_key = from_node_key.replace(" ", "")
        from_node_value = deal_name_dic1[from_node_key]
        if from_node_value is None:
            print(f"error: {from_node_key}")
        from_node_value.set_pName(to_node_key)
        from_node_value.add_parent(to_node_value)
        to_node_value.add_child(from_node_value)

    # model与model之间的关系
    r_cyper1 = f"MATCH (m:`{type}`:{entity_type_str}:Model)-[:REFERENCE_MODEL]->(n:`{type}`:{entity_type_str}:Model) RETURN m,n"
    r_results1 = run_cypher(r_cyper1)

    child_set1 = set()
    parent_set1 = set()
    # 遍历每条边，形成树
    for item in r_results1:
        from_node = item['m']
        to_node = item['n']
        # to_node_key = f"{to_node['名称']}_{to_node['编码']}"
        # parent_set1.add(to_node_key)
        to_node_key = ""
        if '编码' in to_node:
            to_node_key = to_node['编码']
        else:
            print(f"error2-4: {to_node['名称']}")
            to_node_key = to_node['名称']
        to_node_key = to_node_key.replace(" ", "")
        to_node_value = deal_name_dic1[to_node_key]

        from_node_key = ""
        if '编码' in from_node:
            from_node_key = from_node['编码']
        else:
            print(f"error2-5: {from_node['名称']}")
            from_node_key = from_node['名称']
        from_node_key = from_node_key.replace(" ", "")
        from_node_value = deal_name_dic1[from_node_key]
        from_node_value.set_pName(to_node_key)
        from_node_value.add_parent(to_node_value)
        to_node_value.add_child(from_node_value)
    root_val1 = (parent_set1 - child_set1)
    root_val1_result = (all_name_set1 - (parent_set1 | child_set1)) | root_val1

    # 查看是否有的节点，既没有引用model，也没有引用模板
    # TODO
    top_cyper1 = """
        MATCH (n:`{entity_type_str}`:Model:`{type_str}`) 
        WHERE NOT EXISTS {{ 
            MATCH (n)-[:REFERENCE_TEMPLATE]->(:`{entity_type_str}`:Template:`{type_str}`) 
        }} AND NOT EXISTS {{ 
            MATCH (n)-[:REFERENCE_MODEL]->(:`{entity_type_str}`:Model:`{type_str}`) 
        }} 
        RETURN n, apoc.meta.cypher.types(n) AS propTypeMap
        """.format(type_str=type, entity_type_str=entity_type_str)
    top_results1 = run_cypher(top_cyper1)
    for item in top_results1:
        item_node = item['n']
        propTypeMap = item['propTypeMap']
        node_key = ""
        if '编码' in item_node:
            node_key = item_node['编码']
        else:
            print(f"error2-6: {item_node['名称']}")
            node_key = item_node['名称']
        # treeNode = OwlTreeNode(node_key, item_node, 1, pName=type, propTypeMap=propTypeMap)
        treeNode = deal_name_dic1[node_key]
        treeNode.set_pName(type)
        topNode.add_child(treeNode)
    # 所有的实例
    cyper2 = f"MATCH (m:`{type}`:{entity_type_str}:Instance) return m, apoc.meta.cypher.types(m) AS propTypeMap, id(m) as id_m"
    results2 = run_cypher(cyper2)
    deal_name_dic2 = entity_arr[index][2]
    all_name_set2 = set()
    # 处理重名
    for item in results2:
        value = item['m']
        id_m = item['id_m']
        propTypeMap = item['propTypeMap']
        propTypeMap['id'] = 'STRING'
        value['id'] = id_m

        format_name = ""
        if '编码' in value:
            format_name = value['编码']
            # if format_name == 'DC01R0101ADE01M2QA061BC001':
            #     print(f"value:{value}")
        else:
            print(f"error2-7: {value['名称']}")
            format_name = value['名称']

        if type == "故障模式":
            df = pd.DataFrame(columns=["id", "名称", "描述"])
            defect_content = parseDefectById(0, format_name, value['名称'], df)
            # defect_content = '1233'
            value['faultLogicDescription'] = defect_content
            propTypeMap['faultLogicDescription'] = 'STRING'

        if format_name not in deal_name_dic2:
            treeNode = OwlTreeNode(format_name, value, 2, pName="", propTypeMap=propTypeMap)
            deal_name_dic2[format_name] = treeNode
            all_name_set2.add(format_name)

    print(f"Instance count:{len(deal_name_dic2)}")

    # Instance 与 TEMPLATE 之间的关系
    m_cyper1 = f"MATCH (m:`{type}`:{entity_type_str}:Instance)-[:REFERENCE_TEMPLATE]->(n:`{type}`:{entity_type_str}:Template) RETURN m,n"
    m_results1 = run_cypher(m_cyper1)
    for item in m_results1:
        from_node = item['m']
        to_node = item['n']
        # to_node_key = f"{to_node['名称']}_{to_node['编码']}"
        to_node_key = ""
        if '编码' in to_node:
            to_node_key = to_node['编码']
        else:
            print(f"error2-8: {to_node['名称']}")
            to_node_key = to_node['名称']
        to_node_key = to_node_key.replace(" ", "")
        to_node_value = deal_name_dic0[to_node_key]
        if to_node_value is None:
            print(f"error_t1_t0: {to_node_key}")

        from_node_key = ""
        if '编码' in from_node:
            from_node_key = from_node['编码']
        else:
            print(f"error2-9: {from_node['名称']}")
            from_node_key = from_node['名称']
        from_node_key = from_node_key.replace(" ", "")
        from_node_value = deal_name_dic2[from_node_key]
        from_node_value.set_pName(to_node_key)
        from_node_value.add_parent(to_node_value)
        if from_node_value is None:
            print(f"error_t1_from: {from_node_key}")
        to_node_value.add_child(from_node_value)

    # Instance 与 model之间的关系
    t_cyper1 = f"MATCH (m:`{type}`:{entity_type_str}:Instance)-[:REFERENCE_MODEL]->(n:`{type}`:{entity_type_str}:Model) RETURN m,n"
    t_results1 = run_cypher(t_cyper1)
    child_set2 = set()
    parent_set2 = set()
    for item in t_results1:
        from_node = item['m']
        # from_node_id = item['id_m']
        to_node = item['n']
        # to_node_key = f"{to_node['名称']}_{to_node['编码']}"
        to_node_key = ""
        if '编码' in to_node:
            to_node_key = to_node['编码']
        else:
            print(f"error2-10: {to_node['名称']}")
            to_node_key = to_node['名称']
        to_node_key = to_node_key.replace(" ", "")
        to_node_value = deal_name_dic1[to_node_key]
        parent_set2.add(to_node_key)
        if to_node_value is None:
            print(f"error_t1_t0: {to_node_key}")

        from_node_key = ""
        if '编码' in from_node:
            from_node_key = from_node['编码']
        else:
            print(f"error2-11: {from_node['名称']}")
            from_node_key = from_node['名称']
        from_node_key = from_node_key.replace(" ", "")
        from_node_value = deal_name_dic2[from_node_key]
        from_node_value.set_pName(to_node_key)
        from_node_value.add_parent(to_node_value)
        if from_node_value is None:
            print(f"error_t1_from: {from_node_key}")
        to_node_value.add_child(from_node_value)
        child_set2.add(from_node_key)
    # root_val2 = (parent_set2 - child_set2)
    # root_val2_result = (all_name_set2 - (parent_set2 | child_set2)) | root_val
for i in range(len(type_list)):
    deal_subClass_type(i)

for i in range(len(type_list)):
    deal_PartOf(i)

# curIndex = 6
# deal_type(curIndex)

# 遍历tree，生成owl
g = Graph()

# Define namespaces
# Use a generic namespace for the ontology
base_ns = Namespace("http://voc.neo4j.com/datamodel#")
g.bind("", base_ns)
g.bind("owl", OWL)
g.bind("rdfs", RDFS)
g.bind("xsd", XSD)

instance_ns = Namespace("http://voc.neo4j.com/individual#")

annotation_ns = Namespace("http://voc.neo4j.com/annotation#")

# Create the ontology declaration
ontology_uri = URIRef("http://voc.neo4j.com/datamodel")
g.add((ontology_uri, RDF.type, OWL.Ontology))

# Map Neo4j types to XSD types
type_mapping = {
    "STRING": XSD.string,
    "INTEGER": XSD.integer,
    "FLOAT": XSD.float,
    "BOOLEAN": XSD.boolean,
    "DATE": XSD.date,
    "DATETIME": XSD.dateTime,
    "TIME": XSD.time,
    "DURATION": XSD.duration,
    "LONG": XSD.long,
    "DOUBLE": XSD.double,
}

# 找不相关的引用
def mark_reference(index):
    instanceDic = entity_arr[index][2]
    visited = set()

    def dfs_up(current):
        if current in visited:
            return
        visited.add(current)
        current.is_referenced = True
        # 遍历当前节点所有父节点，继续往上追溯
        for p in current.parents:
            dfs_up(p)

    for key, value in instanceDic.items():
        dfs_up(value)

# for i in range(len(type_list)):
#     mark_reference(i)

# 显示引用的,前序遍历
def collect_ref(node, res, visited):
    if  node.type >= -1:
        # if node in visited:
        #     return
        visited.add(node)
        # if node.is_referenced:
            # res.append(node.value)
        if node.type == 2:
            # 2 -- 实例 定义为实例
            instance_uri = instance_ns[node.name]
            p_uri = base_ns[node.pName]
            g.add((instance_uri, RDF.type, p_uri))
            # 给实例增加注释属性
            g.add((instance_uri, RDFS.label, Literal(node.value['名称'], datatype=XSD.string)))
            # 给实例增加属性
            for key, value in node.propTypeMap.items():
                xsd_type = type_mapping.get(value.upper(), XSD.string)
                if key == "createdTime":
                    sec = base_ns[key] // 1_000_000_000
                    dt = datetime.fromtimestamp(sec, tz=timezone.utc)
                    iso_str = dt.strftime('%Y-%m-%dT%H:%M:%S')
                    g.add((instance_uri, base_ns[key], Literal(iso_str, datatype=XSD.dateTime)))
                else:
                    g.add((instance_uri, base_ns[key], Literal(node.value[key], datatype=xsd_type)))
        else:
            # 0和1： 模板和模型，定义为class
            # 子类
            if node.is_referenced or node.type == -1:
                res.append(node.value)
                class_uri = base_ns[node.name]
                g.add((class_uri, RDF.type, OWL.Class))
                if len(node.pName) > 0:
                    g.add((class_uri, RDFS.subClassOf, base_ns[node.pName]))
                else:
                    print(f"no pName: {node.name}")
                    # type_str = type_list[curIndex]
                    # g.add((class_uri, RDF.subClassOf, base_ns[type_str]))

                # 添加属性
                if node.type > -1:
                    g.add((class_uri, RDFS.label, Literal(node.value['名称'], datatype=XSD.string)))
                for key, value in node.propTypeMap.items():
                    prop_uri = base_ns[key]
                    g.add((prop_uri, RDF.type, OWL.DatatypeProperty))
                    g.add((prop_uri, RDFS.domain, class_uri))
                    xsd_type = type_mapping.get(value.upper(), XSD.string)
                    g.add((prop_uri, RDFS.range, xsd_type))



                    # 添加注释
                    class_Annotation = annotation_ns[key]
                    g.add((class_Annotation, RDF.type, OWL.AnnotationProperty))
                    g.add((class_Annotation, RDFS.label, Literal(key)))
                    if key == "createdTime":
                        ns_ts = 0
                        try:
                            ns_ts = int(value)
                        except Exception as e:
                            print(e)
                        sec = ns_ts / 1_000_000_000
                        dt = datetime.fromtimestamp(sec, tz=timezone.utc)
                        iso_str = dt.strftime('%Y-%m-%dT%H:%M:%S')
                        g.add((class_uri, class_Annotation, Literal(iso_str, datatype=XSD.dateTime)))
                    else:
                        if key == '测点类型（DCS）':
                            continue
                        g.add((class_uri, class_Annotation, Literal(node.value[key], datatype=xsd_type)))
    for c in node.children:
        collect_ref(c, res, visited)

# ref_list = []
# collect_ref(tree.root, ref_list, set())
# print(len(ref_list))


def check_same(node, time):
    if node.type == 1 and len(node.children) > 1:
        isSame = True
        name = ''
        for c in node.children:
            if c.type == 2:
                isSame = False
                break
            if len(c.partOfTo) > 0:
                if len(name) == 0:
                    name = c.partOfTo[0].name
                else:
                    if name != c.partOfTo[0].name:
                        isSame = False
                        break
            else:
                isSame = False
                break
        if isSame:
            print(f"same part: {node.name}, time: {time}, type: {node.type}")
            node.partOfTo.append(node.children[0].partOfTo[0])
            print(f"new part: {node.partOfTo[0].name}")
            for c in node.children:
                print(f"old child: {c.name}, name:{c.partOfTo[0].name}")
                c.partOfTo = []
    for c in node.children:
        check_same(c, time)
# 前序遍历
def pre_order(node, level=0):
    if level  > 20:
        print(f"node: {node}")

    # if len(node.children) > 1:
    #     isSame = True
    #     name = ''
    #     # partOfToCount = 0
    #     for c in node.children:
    #         if len(c.partOfTo) > 0:
    #             # partOfToCount += 1
    #             if len(name) == 0:
    #                 name = c.partOfTo[0].name
    #             else:
    #                 if name != c.partOfTo[0].name:
    #                     isSame = False
    #                     break
    #         else:
    #             isSame = False
    #             break
    #     if isSame:
    #         print(f"same part: {node.name}")
    #
    #         node.partOfTo.append(node.children[0].partOfTo[0])
    #         for c in node.children:
    #             c.partOfTo = []

    if node.type >= -1:
        class_uri = base_ns[node.name]
        if node.type == 2:
            # 2 -- 实例 定义为实例
            instance_uri = instance_ns[node.name]
            p_uri = base_ns[node.pName]
            g.add((instance_uri, RDF.type, p_uri))
            # 给实例增加注释属性
            g.add((instance_uri, RDFS.label, Literal(node.value['名称'], datatype=XSD.string)))

            for key, value in node.propTypeMap.items():
                # print(f"key: {key}")

                # if len(node.value[key]) == 0:
                #     continue
                # g.add((instance_uri, base_ns[key], Literal(node.value[key], datatype=xsd_type)))
                if key == "createdTime":
                    sec = 0
                    try:
                        sec = int(node.value[key] / 100000000)
                    except Exception as e:
                        print(e)
                    dt = datetime.fromtimestamp(sec, tz=timezone(timedelta(hours=8)))
                    iso_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                    g.add((instance_uri, base_ns[key], Literal(iso_str, datatype=XSD.string)))
                else:
                    if key == '测点类型（DCS）':
                        continue
                    xsd_type = XSD.string
                    try:
                        xsd_type = type_mapping.get(value.upper(), XSD.string)
                    except Exception as e:
                        print(f"error111: {key}")
                    g.add((instance_uri, base_ns[key], Literal(node.value[key], datatype=xsd_type)))

        else:
            # 0和1： 模板和模型，定义为class
            # 子类
            g.add((class_uri, RDF.type, OWL.Class))
            if len(node.pName) > 0:
                g.add((class_uri, RDFS.subClassOf, base_ns[node.pName]))
                # if len(node.parents) > 1:
                #     print(f"node1: {node.name}")

            # prop_uri = base_ns['modelFaultLogicDescription']
            # 添加属性
            if node.type > -1:
                g.add((class_uri, RDFS.label, Literal(node.value['名称'], datatype=XSD.string)))
            for key, value in node.propTypeMap.items():
                xsd_type = type_mapping.get(value.upper(), XSD.string)
                prop_uri = base_ns[key]
                g.add((prop_uri, RDF.type, OWL.DatatypeProperty))
                # g.add((prop_uri, RDFS.domain, class_uri))
                # g.add((prop_uri, RDFS.range, xsd_type))

                if key == 'modelFaultLogicDescription':
                    # 添加class约束
                    restriction_class1 = BNode()
                    g.add((restriction_class1, RDF.type, OWL.Restriction))
                    g.add((restriction_class1, OWL.onProperty, prop_uri))
                    g.add((class_uri, RDFS.subClassOf, restriction_class1))
                    g.add((restriction_class1, OWL.hasValue, Literal(node.value[key], datatype=xsd_type)))

                if value == "STRING" and len(node.value[key]) == 0:
                    continue
                # 添加注释
                class_Annotation = annotation_ns[key]
                g.add((class_Annotation, RDF.type, OWL.AnnotationProperty))
                g.add((class_Annotation, RDFS.label, Literal(key)))
                if key == "createdTime":
                    sec = 0
                    try:
                        sec = int(node.value[key] / 100000000)
                    except Exception as e:
                        print(e)
                    dt = datetime.fromtimestamp(sec, tz=timezone(timedelta(hours=8)))
                    iso_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                    g.add((class_uri, class_Annotation, Literal(iso_str, datatype=XSD.string)))
                else:
                    g.add((class_uri, class_Annotation, Literal(node.value[key], datatype=xsd_type)))
            prop_uri_id = base_ns["id"]
            g.add((prop_uri_id, RDF.type, OWL.DatatypeProperty))

            prop_uri_faultLogicDescription = base_ns["faultLogicDescription"]
            g.add((prop_uri_faultLogicDescription, RDF.type, OWL.DatatypeProperty))

            # 故障模式model的注释属性
            # if node.type == 1:
            #     defect_Annotation_uri = annotation_ns["modelFaultLogicDescription"]
            #     g.add((defect_Annotation_uri, RDF.type, OWL.AnnotationProperty))
            #     # 获取故障模式的描述
            #     df = pd.DataFrame(columns=["id", "名称", "描述"])
            #     defect_content = parseDefectById(0, node.value['编码'], node.value['名称'], df)
            #     g.add((defect_Annotation_uri, RDFS.label, Literal("modelFaultLogicDescription")))
            #     g.add((class_uri, defect_Annotation_uri, Literal(defect_content, datatype=XSD.string)))

        # 添加关系
        for part in node.partOfTo:
            if node.type == 2:
                type_str = 'belongsTo'
                if '类别' in node.value:
                    if node.value['类别'] == '故障模式':
                        type_str = 'defect_belongsTo'


                # 实例
                # print("aa")
                belongsTo = base_ns[type_str]
                g.add((belongsTo, RDF.type, OWL.TransitiveProperty))
                instance_uri = instance_ns[node.name]
                partToUri = instance_ns[part.name]
                g.add((instance_uri, belongsTo, partToUri))
            else:
                type_str = 'partOf'
                if '类别' in node.value:
                    if node.value['类别'] == '故障模式':
                        type_str = 'defect_partOf'
                part_of = base_ns[type_str]
                g.add((part_of, RDF.type, OWL.TransitiveProperty))
                g.add((part_of, RDFS.domain, class_uri))
                partToUri = base_ns[part.name]
                g.add((part_of, RDFS.range, partToUri))

    for c in node.children:
        pre_order(c, level + 1)

check_same(tree.root, 1)
check_same(tree.root, 2)

# 前序遍历
pre_order(tree.root, 0)

result_str = g.serialize(format="turtle")

with open('dam.ttl', 'w', encoding="utf-8") as f:
    f.write(result_str)

result_str1 = g.serialize(format="xml")
with open('dam.owl', 'w', encoding="utf-8") as f:
    f.write(result_str1)

driver.close()