from neo4j import GraphDatabase

from neo4jonth.OwlTree import OwlTree
from neo4jonth.OwlTreeNode import OwlTreeNode
from rdflib import OWL, RDF, RDFS, XSD, Graph, Namespace, URIRef, Literal

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

# 所有的顶层集合
# 电厂
powerplant_OwlTree = OwlTree("root")
unit_OwlTree = OwlTree("root")

# 要处理名称重复
def deal_type(type):
    # global powerplant_OwlTree
    # 模板
    cyper0 = f"MATCH (m:`{type}`:Entity:Template) return m, apoc.meta.cypher.types(m) AS propTypeMap"
    results0 = run_cypher(cyper0)
    tree = OwlTree("root")
    # nameSet0 = set()
    # sameNameSet0 = set()
    # for item in results0:
    #     value = item['m']
    #     format_name = f"{value['名称']}_{value['编码']}"
    #     if format_name in nameSet0:
    #         print(f"0： {value}")
    #         sameNameSet0.add(format_name)
    #     else:
    #         nameSet0.add(format_name)

    deal_name_dic0 = {}
    # 处理重名
    for item in results0:
        value = item['m']
        propTypeMap = item['propTypeMap']
        format_name = f"{value['名称']}_{value['编码']}"
        if format_name not in deal_name_dic0:
            treeNode = OwlTreeNode(format_name, value, 0, pName="", propTypeMap=propTypeMap)
            deal_name_dic0[format_name] = treeNode
            # 查属性
            tree.root.add_child(treeNode)

    # 模型 -先所有的
    cyper1 = f"MATCH (m:`{type}`:Entity:Model) return m, apoc.meta.cypher.types(m) AS propTypeMap"
    results1 = run_cypher(cyper1)
    # list_1 =[]
    # nameSet1 = set()
    # sameNameSet1 = set()
    # for item in results1:
    #     value = item['m']
    #     if value['名称'] in nameSet1:
    #         print(f"1： {value}")
    #         sameNameSet1.add(value['名称'])
    #     else:
    #         nameSet1.add(value['名称'])

    # model所有的，的字典，key：名称， value： 节点
    deal_name_dic1 = {}
    all_name_set1 = set()

    for item in results1:
        value = item['m']
        propTypeMap = item['propTypeMap']
        format_name = f"{value['名称']}_{value['编码']}"
        if format_name not in deal_name_dic0:
            treeNode = OwlTreeNode(format_name, value, 1, pName="", propTypeMap=propTypeMap)
            deal_name_dic1[format_name] = treeNode
            all_name_set1.add(format_name)


        # if value['名称'] in sameNameSet0:
        #     name = f"{value['名称']}-{value['编码']}"
        # else:
        #     name = value['名称']
        # if name not in deal_name_dic1:
        #     deal_name_dic1[name] = OwlTreeNode(value['名称'], value, 1)
        #     all_name_set.add(name)
            # list_1.append(treeNode)

    # model 与 模板之间的层级关系
    t_cyper1 = f"MATCH (m:`{type}`:Entity:Model)-[:REFERENCE_TEMPLATE]->(n:`{type}`:Entity:Template) RETURN m,n"
    t_results1 = run_cypher(t_cyper1)

    for item in t_results1:
        from_node = item['m']
        to_node = item['n']
        to_node_key = f"{to_node['名称']}_{to_node['编码']}"
        to_node_value = deal_name_dic0[to_node_key]
        if to_node_value is None:
            print(f"error1: {to_node_key}")

        from_node_key = f"{from_node['名称']}_{from_node['编码']}"
        from_node_value = deal_name_dic1[from_node_key]
        if from_node_value is None:
            print(f"error: {from_node_key}")
        from_node_value.set_pName(to_node_key)
        to_node_value.add_child(from_node_value)

    # model之间的关系
    r_cyper1 = f"MATCH (m:`{type}`:Entity:Model)-[:REFERENCE_MODEL]->(n:`{type}`:Entity:Model) RETURN m,n"
    r_results1 = run_cypher(r_cyper1)

    child_set1 = set()
    parent_set1 = set()
    # 遍历每条边，形成树
    for item in r_results1:
        from_node = item['m']
        to_node = item['n']
        to_node_key = f"{to_node['名称']}_{to_node['编码']}"
        # parent_set1.add(to_node_key)
        to_node_value = deal_name_dic1[to_node_key]

        from_node_key = f"{from_node['名称']}_{from_node['编码']}"
        # child_set1.add(from_node_key)
        from_node_value = deal_name_dic1[from_node_key]
        from_node_value.set_pName(to_node_key)
        to_node_value.add_child(from_node_value)
    # root_val1 = (parent_set1 - child_set1)
    # root_val1_result = (all_name_set1 - (parent_set1 | child_set1)) | root_val1

    # 查看是否有的节点，既没有引用model，也没有引用模板
    # TODO



    # 实例
    cyper2 = f"MATCH (m:`{type}`:Entity:Instance) return m, apoc.meta.cypher.types(m) AS propTypeMap"
    results2 = run_cypher(cyper2)
    # list_2 =[]
    # nameSet2 = set()
    # sameNameSet2 = set()
    # for item in results2:
    #     value = item['m']
    #     if value['名称'] in nameSet2:
    #         print(f"2： {value}")
    #         sameNameSet2.add(value['名称'])
    #     else:
    #         nameSet2.add(value['名称'])

    # deal_name_set2 = set()
    deal_name_dic2 = {}
    all_name_set2 = set()
    # 处理重名
    for item in results2:
        value = item['m']
        propTypeMap = item['propTypeMap']
        format_name = f"{value['名称']}_{value['编码']}"
        if format_name not in deal_name_dic2:
            treeNode = OwlTreeNode(format_name, value, 2, pName="", propTypeMap=propTypeMap)
            deal_name_dic2[format_name] = treeNode
            all_name_set2.add(format_name)
        # name = ''
        # if value['名称'] in sameNameSet2:
        #     name = f"{value['名称']}-{value['编码']}"
        # else:
        #     name = value['名称']
        # if name not in deal_name_set2:
        #     deal_name_set2.add(name)
        #     treeNode = OwlTreeNode(value['名称'], value, 2)
        #     list_2.append(treeNode)

    # Instance 与 TEMPLATE 之间的关系
    m_cyper1 = f"MATCH (m:`{type}`:Entity:Instance)-[:REFERENCE_TEMPLATE]->(n:`{type}`:Entity:Template) RETURN m,n"
    m_results1 = run_cypher(m_cyper1)
    for item in m_results1:
        from_node = item['m']
        to_node = item['n']
        to_node_key = f"{to_node['名称']}_{to_node['编码']}"
        to_node_value = deal_name_dic0[to_node_key]
        if to_node_value is None:
            print(f"error_t1_t0: {to_node_key}")

        from_node_key = f"{from_node['名称']}_{from_node['编码']}"
        from_node_value = deal_name_dic2[from_node_key]
        from_node_value.set_pName(to_node_key)
        if from_node_value is None:
            print(f"error_t1_from: {from_node_key}")
        to_node_value.add_child(from_node_value)

    # Instance 与 model之间的关系
    t_cyper1 = f"MATCH (m:`{type}`:Entity:Instance)-[:REFERENCE_MODEL]->(n:`{type}`:Entity:Model) RETURN m,n"
    t_results1 = run_cypher(t_cyper1)
    child_set2 = set()
    parent_set2 = set()
    for item in t_results1:
        from_node = item['m']
        to_node = item['n']
        to_node_key = f"{to_node['名称']}_{to_node['编码']}"
        to_node_value = deal_name_dic1[to_node_key]
        parent_set2.add(to_node_key)
        if to_node_value is None:
            print(f"error_t1_t0: {to_node_key}")

        from_node_key = f"{from_node['名称']}_{from_node['编码']}"
        from_node_value = deal_name_dic2[from_node_key]
        from_node_value.set_pName(to_node_key)
        if from_node_value is None:
            print(f"error_t1_from: {from_node_key}")
        to_node_value.add_child(from_node_value)
        child_set2.add(from_node_key)
    # root_val2 = (parent_set2 - child_set2)
    # root_val2_result = (all_name_set2 - (parent_set2 | child_set2)) | root_val

    return tree
tree = deal_type('系统')

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

def print_tree(node):
    if node.type > -1:
        if node.type == 2:
            # 2 -- 实例 定义为实例
            instance_uri = instance_ns[node.name]
            p_uri = base_ns[node.pName]
            g.add((instance_uri, RDF.type, p_uri))
            # 给实例增加属性
            for key, value in node.propTypeMap.items():
                xsd_type = type_mapping.get(value.upper(), XSD.string)
                g.add((instance_uri, base_ns[key], Literal(node.value[key], datatype=xsd_type)))
        else:
            # 0和1： 模板和模型，定义为class
            # 子类
            class_uri = base_ns[node.name]
            g.add((class_uri, RDF.type, OWL.Class))
            if len(node.pName) > 0:
                g.add((class_uri, RDFS.subClassOf, base_ns[node.pName]))
            # 添加属性

            g.add((class_uri, RDFS.label, Literal(node.value['名称'])))
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

                g.add((class_uri, class_Annotation, Literal(node.value[key], datatype=xsd_type)))

    for c in node.children:
        print_tree(c)

print_tree(tree.root)

result_str = g.serialize(format="turtle")

with open('example4.ttl', 'w', encoding="utf-8") as f:
    f.write(result_str)

driver.close()