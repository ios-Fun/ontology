# 故障模式转自然语言，不调用dam

from neo4j import GraphDatabase

from neo4jonth.OwlTree import OwlTree
from neo4jonth.OwlTreeNode import OwlTreeNode
from rdflib import OWL, RDF, RDFS, XSD, Graph, Namespace, URIRef, Literal
from datetime import datetime, timezone, timedelta
import requests

from neo4jonth.defect.DefectTree import DefectTree
from neo4jonth.defect.DefectTreeNode import DefectTreeNode
import pandas as pd
# URI = "bolt://192.168.0.54:7687"
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

def tree_depth(node, level) -> int:
    max_child_depth = level
    for child in node.children:
        if child.type ==0:
            if child.name == "与" or child.name == "或" or child.name == "N取M":
                d = tree_depth(child, level+1)
                if d > max_child_depth:
                    max_child_depth = d
    return max_child_depth

# 第二层的与模块-带数字
def useSubAndMoudle(return_str, treeNode, level,maxDepth, index):
    return_str += f"以下{numToChinese(len(treeNode.children))}类子工况同时发生\n"
    for item in treeNode.children:
        child_str = getResultFromChild(item, level + 1, maxDepth, False)[0]
        if len(child_str) == 0:
            continue
        return_str += f"{num_to_circle(index + 1, level)}"

        if not (check_last_punct(child_str)):
            # if index == len(treeNode.children) - 1:
            #     child_str += "，"
            if index >= 0:
                child_str += "；"

        return_str += child_str
        if not return_str.endswith('\n'):
            return_str += "\n"
        index = index + 1
    return return_str

# 第二层的或模块-带数字
def useSubOrMoudle(return_str, treeNode, level,maxDepth, index):
    return_str += f"以下{numToChinese(len(treeNode.children))}类子工况任意一类发生\n"
    for item in treeNode.children:
        child_str = getResultFromChild(item, level + 1, maxDepth, False)[0]
        if len(child_str) == 0:
            continue
        return_str += f"{num_to_circle(index + 1, level)}"

        if not (check_last_punct(child_str)):
            # if index == len(treeNode.children) - 1:
            #     child_str += "，"
            if index >= 0:
                child_str += "；"

        return_str += child_str
        if not return_str.endswith('\n'):
            return_str += "\n"
        index = index + 1
    return return_str

# 与模板
def useAndMoudle(defect_name, firstChildren, maxDepth, defecId, df):
    result_str = f"{defect_name}需要同时满足以下{numToChinese(len(firstChildren))}组条件："
    result_str += "\n"
    for i in range(len(firstChildren)):
        item_str = getResultFromChild(firstChildren[i], 1, maxDepth,False)[0]
        item_f = ""
        if "①" in item_str:
            item_f = f"条件组{numToChinese(i + 1)}：{strip_end_punctuation(item_str)}\n"
        else:
            item_f = strip_second_end_punctuation(f"条件组{numToChinese(i + 1)}：{item_str}。\n")
        result_str += item_f
    result_str += f"{numToChinese(len(firstChildren))}组条件同时满足时，可能发生{defect_name}。"
    new_row = pd.DataFrame([{"id": defecId, "名称": defect_name, "描述": result_str}])
    # df = pd.concat([df, new_row], ignore_index=True)
    df.loc[len(df)] = [defecId, defect_name, result_str]
    print(result_str)
    return result_str

# 去掉尾部的符号
def strip_end_punctuation(text):
    punct = "，。；：？！、"
    if text and text[-1] in punct:
        return text[:-1]
    return text

# 去掉尾部的-倒数第二个符号
def strip_second_end_punctuation(text):
    # 定义需要识别的标点
    punct = {"，", "。", "；", "：", "？", "！", "、"}
    if text.endswith('\n'):
        # 末尾带换行：判断倒数第3位是不是标点，是则删掉倒数第3个字符
        if len(text) >= 3 and text[-3] in punct:
            return text[:-3] + text[-2:]
    else:
        # 不带换行：判断倒数第2位是不是标点，是则删掉倒数第2个字符
        if len(text) >= 2 and text[-2] in punct:
            return text[:-2] + text[-1:]
    return text

# 判断最后一个字符是否为标点
def check_last_punct(text):
    # 定义标点集合
    punct = {"，", "。", "；", "：", "？", "！", "、"}
    if not text:  # 空字符串直接返回False
        return False
    if text.endswith('\n'):
        return text[-2] in punct
    else:
        return text[-1] in punct

# 判断字符串是否以同时开头
def start_with_tongshi(text):
    return text.startswith("同时")

# def sortChildren(children):

# 根据故障模式id得到tree
def parseDefectTreeById(defectId, code):
    print(f"defectId: {defectId}, code: {code}")
    shadow_cyper1 = ''
    if len(code) == 0:
        shadow_cyper1 = f"MATCH(m) -[r: REFERENCE_SHADOW]->(n) where id(n)={defectId} return m, id(m) as id_m"
    else:
        shadow_cyper1 = f"MATCH(m) -[r: REFERENCE_SHADOW]->(n) where n.编码='{code}' return m, id(m) as id_m"
    shadow_results = run_cypher(shadow_cyper1)
    defectTree = DefectTree("root")
    for res1 in shadow_results:
        shadow_m = res1["id_m"]
        getChildren(shadow_m, defectTree.root)
    return defectTree


# 根据故障模式id得到自然语言
def parseDefectById(defecId, code, defect_name, df):
    # 先得到故障模式 shadow
    shadow_cyper1 = ''
    if len(code) == 0:
        shadow_cyper1 = f"MATCH(m) -[r: REFERENCE_SHADOW]->(n) where id(n)={defecId} return m, id(m) as id_m"
    else:
        shadow_cyper1 = f"MATCH(m) -[r: REFERENCE_SHADOW]->(n) where n.编码='{code}' return m, id(m) as id_m"
    shadow_results = run_cypher(shadow_cyper1)
    defectTree = DefectTree("root")
    for res1 in shadow_results:
        shadow_m = res1["id_m"]
        getChildren(shadow_m, defectTree.root)

    # 获取树的深度
    maxDepth = tree_depth(defectTree.root, 0)

    if maxDepth > 3:
        print("warn 4")
    # 解析 tree
    if len(defectTree.root.children) > 1 or len(defectTree.root.children) == 0:
        print(f"warn_a: {defect_name}")
    else:
        # 先深度遍历第一层
        name = defectTree.root.children[0].name
        firstChildren = defectTree.root.children[0].children
        if name == "与":
            if maxDepth <= 2:
                # 如果第二层有或节点，并且或节点的分支大>=3
                and_flag = False
                for child in firstChildren:
                    if child.type == 0 and child.name == "或" and len(child.children) > 2:
                        and_flag = True
                if and_flag:
                    return useAndMoudle(defect_name, firstChildren, maxDepth,defecId, df)
                else:
                    if len(firstChildren) == 1:
                        # 首层与节点只有一个
                        # 模板： 当{}时，可能导致{}发生
                        str_list = getResultFromChild(firstChildren[0], 1, maxDepth, True)
                        str = str_list[0]
                        return_str = f"当{strip_end_punctuation(str)}时，可能导致{defect_name}发生"
                        n_of_m_list = []
                        if len(str_list) == 4:
                            if len(n_of_m_list) != 0:
                                print("error to long")
                            n_of_m_list = str_list[3]
                        if len(n_of_m_list) == 0:
                            return_str += "。"
                        else:
                            return_str += "：\n"
                            for i in range(len(n_of_m_list)):
                                return_str += f"{i+1}.{n_of_m_list[i]}"
                                if i == len(n_of_m_list) - 1:
                                    return_str += "。\n"
                                else:
                                    return_str += ";\n"
                        print(return_str)
                        new_row = pd.DataFrame([{"id": defecId, "名称": defect_name, "描述": return_str}])
                        # df = pd.concat([df, new_row], ignore_index=True)
                        df.loc[len(df)] = [defecId, defect_name, return_str]
                        return return_str
                    else:
                        return_str = "当"
                        index = 0
                        n_of_m_list =[]

                        firstChildren.sort(key=lambda x: x.name == "N取M")
                        # 或放在前面
                        firstChildren.sort(key=lambda x: x.name != "或")
                        count = sum(1 for x in firstChildren if x.name == "N取M")
                        if count > 1:
                            return useAndMoudle(defect_name, firstChildren, maxDepth,defecId, df)
                        else:
                            orCount = 0
                            for item in firstChildren:
                                if item.type == 0 and item.name == "或":
                                    orCount += 1
                            if orCount > 1:
                                return useAndMoudle(defect_name, firstChildren, maxDepth, defecId, df)
                            else:
                                for item in firstChildren:
                                    str_list = getResultFromChild(item, 1, maxDepth, True)
                                    if len(str_list) == 4:
                                        if len(n_of_m_list) != 0:
                                            print("error to long")
                                        n_of_m_list = str_list[3]
                                    child_str = str_list[0]
                                    if len(child_str) == 0:
                                        continue
                                    if index == 1:
                                        if "①" in return_str:
                                            return_str += "且"
                                        else:
                                            return_str += "，且"
                                    if index > 1:
                                        return_str += "、"
                                    return_str += strip_end_punctuation(child_str)
                                    index = index + 1
                                return_str += f"时，可能导致{defect_name}发生"
                                if len(n_of_m_list) == 0:
                                    return_str += "。"
                                else:
                                    return_str += "：\n"
                                    for i in range(len(n_of_m_list)):
                                        return_str += f"{i+1}.{n_of_m_list[i]}"
                                        if i == len(n_of_m_list) - 1:
                                            return_str += "。\n"
                                        else:
                                            return_str += ";\n"

                                new_row = pd.DataFrame([{"id": defecId, "名称": defect_name, "描述": return_str}])
                                # df = pd.concat([df, new_row], ignore_index=True)
                                df.loc[len(df)] = [defecId, defect_name, return_str]
                                print(return_str)
                                return return_str
            elif maxDepth == 3:
                # 换模板
                if len(firstChildren) == 1:
                    print("warn 12")
                else:
                    return useAndMoudle(defect_name, firstChildren, maxDepth,defecId, df)

        elif name == "或":
            if len(firstChildren) == 1:
                print("warn 11")
            else:
                # 模板
                result_str= f"{defect_name}可能由以下{numToChinese(len(firstChildren))}种情况引发："
                result_str += "\n"
                for i in range(len(firstChildren)):
                    item_str = strip_second_end_punctuation(getResultFromChild(firstChildren[i], 1, maxDepth, False)[0])
                    if "①" in item_str:
                        item_f = f"第{numToChinese(i + 1)}种：{strip_end_punctuation(item_str)}\n"
                    else:
                        if check_last_punct(item_str):
                            item_f = f"第{numToChinese(i + 1)}种：{item_str}\n"
                        else:
                            item_f = f"第{numToChinese(i + 1)}种：{item_str}；\n"

                    result_str += item_f
                result_str += f"当上述{numToChinese(len(firstChildren))}种情况中的任意一种出现时，可能发生{defect_name}。"
                print(result_str)
                new_row = pd.DataFrame([{"id": defecId, "名称": defect_name, "描述": result_str}])
                # df = pd.concat([df, new_row], ignore_index=True)
                df.loc[len(df)] = [defecId, defect_name, result_str]
                return result_str
        elif name == "大于":
            return_str = "当"
            child = firstChildren[0]
            child_str = getResultFromChild(child, 1, maxDepth, False)[0]
            operateParameter = defectTree.root.children[0].valueDic['operateParameter']
            return_str += f"{child_str}{defectTree.root.children[0].name}{operateParameter}"
            return_str += f"时，可能导致{defect_name}发生。"
            print(return_str)
            new_row = pd.DataFrame([{"id":defecId, "名称":defect_name, "描述":return_str}])
            # df = pd.concat([df, new_row], ignore_index=True)
            df.loc[len(df)] = [defecId, defect_name, return_str]
            return return_str
        elif name == "N取M":
            result_str = f"{defect_name}可能由以下{numToChinese(len(firstChildren))}种情况引发："
            result_str += "\n"
            for i in range(len(firstChildren)):
                item_str = getResultFromChild(firstChildren[i], 1, maxDepth, False)[0]
                item_f = f"第{numToChinese(i + 1)}种：{item_str}；\n"
                result_str += item_f
            operateParameter = int(defectTree.root.children[0].valueDic['operateParameter'])
            if operateParameter == 1:
                result_str += f"当上述{numToChinese(len(firstChildren))}种情况中的任意{numToChinese(operateParameter)}种出现时，可能发生{defect_name}。"
                # desc_str = f'同时满足以下{numToChinese(len(treeNode.children))}项异常中至少{numToChinese(operateParameter)}项出现'
            else:
                if len(firstChildren) < operateParameter:
                    result_str += f"当上述{numToChinese(len(firstChildren))}种情况中的任意{numToChinese(operateParameter)}种出现时，可能发生{defect_name}。"
                    # desc_str = f'同时满足以下{numToChinese(len(treeNode.children))}项异常中至少{numToChinese(operateParameter)}项同时出现'
                else:
                    result_str += f"当上述{numToChinese(len(firstChildren))}种情况中都出现时，可能发生{defect_name}。"
                    # desc_str = f'同时满足以下{numToChinese(len(treeNode.children))}项异常'

            print(result_str)
            new_row = pd.DataFrame([{"id": defecId, "名称": defect_name, "描述": result_str}])
            # df = pd.concat([df, new_row], ignore_index=True)
            df.loc[len(df)] = [defecId, defect_name, result_str]
            return result_str
        else:
            print(f"error 12: {name}")
    return ""

# 状态有或修改
def formatStatus(status):
    res = status.replace("|", "或")
    return res

def num_to_circle(n: int, level) -> str:
    """把数字转为 ①②③…⑳，大于20返回(21)"""
    if level <=1:
        table = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
        if 1 <= n <= 20:
            return table[n - 1]
        return f"({n})"
    else:
        return f"({n})"

# 数字转中文
def numToChinese(index):
    if index == 1:
        return "一"
    elif index == 2:
        return "二"
    elif index == 3:
        return "三"
    elif index == 4:
        return "四"
    elif index == 5:
        return "五"
    elif index == 6:
        return "六"
    elif index == 7:
        return "七"
    elif index == 8:
        return "八"
    elif index == 9:
        return "九"
    elif index == 10:
        return "十"
    elif index == 11:
        return "十一"
    elif index == 12:
        return "十二"
    elif index == 13:
        return "十三"
    elif index == 14:
        return "十四"
    elif index == 15:
        return "十五"
    elif index == 16:
        return "十六"
    elif index == 17:
        return "十七"
    elif index == 18:
        return "十八"
    elif index == 19:
        return "十九"
    elif index == 20:
        return "二十"
    elif index == 21:
        return "二十一"
    else:
        print(f"error1: {index}")
        return ""

# 查询所有故障模式
def queryAllDefectsMode():
    print("queryAllDefectsMode")
    # Instance / Model
    t_cyper1 = "MATCH (m:Logic:Model:故障模式) RETURN m, id(m) as id_m"
    results = run_cypher(t_cyper1)
    df = pd.DataFrame(columns=["id", "名称", "描述"])
    for res in results:
        print("")
        print(res["id_m"])
        defect_name = res["m"]["名称"].strip()
        print(defect_name)
        id_m = res["id_m"]
        parseDefectById(id_m,'', defect_name, df)
    df.to_csv("data.csv", index=False, encoding="utf-8-sig")

# 获取次层节点的显示
def getResultFromChild(treeNode, level, maxDepth, isFirstAnd: False):
    if level >2:
        print(f"warn1: {level}")
    if treeNode.type == 1:
        # 表示特征
        desc_str = ""
        status = treeNode.status
        name = treeNode.name
        if "、" in name:
            name = f'“{name}”'
        if status is not None and len(status) >0:
            desc_str = f"{name}{formatStatus(status)}"
            return [desc_str, name, formatStatus(status)]
        else:
            desc_str = name
            return [desc_str, "", ""]
    else:
        if treeNode.name == "等于比较":
            if len(treeNode.children) > 0:
                child_str = ""
                child_str += getResultFromChild(treeNode.children[0],level, maxDepth, False)[0]
                # print(f"child_str1:{child_str}")
                operateParameter = int(treeNode.valueDic['operateParameter'])
                return [f"{child_str}等于{operateParameter}", child_str,  f"等于{operateParameter}"]
            else:
                return ["", "", ""]
        elif treeNode.name == "与":
            # 第二层的与
            return_str = ""
            index = 0

            if maxDepth == 3 and level == 2 and len(treeNode.children) > 2:
                # 第三层的and
                return_str += f"同时满足以下{numToChinese(len(treeNode.children))}项条件："
            if level == 1 and maxDepth == 3:
                return_str += useSubAndMoudle(return_str, treeNode, level,maxDepth, index)
            else:

                for item in treeNode.children:
                    child_str = ""
                    child_str += getResultFromChild(item, level+1, maxDepth, False)[0]
                    # print(f"child_str2:{child_str}")

                    if maxDepth == 3 and level == 2 and len(treeNode.children) > 2:
                        # 是第三层的and
                        if index == 1:
                            return_str += "、"
                        elif index == len(treeNode.children) - 1:
                            return_str += "，以及"

                    else:
                        if index == 1:
                            if maxDepth > 2:
                                if level == 2:
                                    if not start_with_tongshi(child_str):
                                        return_str += "同时"
                                else:
                                    # 当前是第二层，还有下一层
                                    if not start_with_tongshi(child_str):
                                        return_str += "，同时"
                                    else:
                                        return_str += "，"
                            else:
                                if not start_with_tongshi(child_str):
                                    return_str += "，同时"
                                else:
                                    return_str += "，"
                        if index > 1:
                            return_str += "、"
                    return_str += child_str
                    index = index + 1
                #if index < len(treeNode.children)-1:
            return_str += "；"
            return [return_str, "",""]
        elif treeNode.name == "大于" or treeNode.name == "大于等于" or treeNode.name == "小于" or treeNode.name == "小于等于" :
            if len(treeNode.children) == 0:
                return ["", "", ""]
            child =  treeNode.children[0]
            child_str = getResultFromChild(child, level, maxDepth, False)[0]
            operateParameter = int(treeNode.valueDic['operateParameter'])
            return [f"{child_str}{treeNode.name}{operateParameter}", child_str, f"{treeNode.name}{operateParameter}"]
        elif treeNode.name == "减号":
            return_str = ""
            index = 0
            for item in treeNode.children:
                child_str = ""
                child_str += getResultFromChild(item, level, maxDepth, False)[0]
                if index >= 1:
                    return_str += "与"
                return_str += child_str
                index = index + 1
            return_str += "之差"
            return [return_str, "", ""]
        elif treeNode.name == "N取M":
            print("warn N取M")
            if 'operateParameter' not in treeNode.valueDic:
                return ["", "", ""]
            operateParameter = int(treeNode.valueDic['operateParameter'])
            if isFirstAnd:
                # 首层and下的
                return_str = ""
                if operateParameter == 1:
                    desc_str = f'同时满足以下{numToChinese(len(treeNode.children))}项异常中至少{numToChinese(operateParameter)}项出现'
                else:
                    if len(treeNode.children) < operateParameter:
                        desc_str = f'同时满足以下{numToChinese(len(treeNode.children))}项异常中至少{numToChinese(operateParameter)}项同时出现'
                    else:
                        desc_str = f'同时满足以下{numToChinese(len(treeNode.children))}项异常'

                return_str += desc_str
                n_of_m_list = []
                for item in treeNode.children:
                    child_str = getResultFromChild(item, level, maxDepth,False)[0]
                    n_of_m_list.append(child_str)
                return [return_str, "", "", n_of_m_list]
            else:
                # 其他
                return_str = ""
                index = 0
                for item in treeNode.children:
                    child_str = getResultFromChild(item, level, maxDepth,False)[0]
                    if index >= 1:
                        return_str += "、"
                    return_str += child_str
                    index = index + 1

                desc_str = ''
                if operateParameter == 1:
                    desc_str = f'，同时满足上述{numToChinese(len(treeNode.children))}项异常中至少{numToChinese(operateParameter)}项出现'
                else:
                    if len(treeNode.children) < operateParameter:
                        desc_str = f'，同时满足上述{numToChinese(len(treeNode.children))}项异常中至少{numToChinese(operateParameter)}项同时出现'
                    else:
                        desc_str = f'，同时满足上述{numToChinese(len(treeNode.children))}项异常'

                return_str += desc_str
                return [return_str, "", ""]
        elif treeNode.name == "或":
            # 第二-三层或
            return_str = ""
            index = 0

            # 或的分支有三个及以上
            # 或是否采用数字分开
            use_number_or= False
            if len(treeNode.children) > 2:
                use_number_or = True

            # 如果下面的or有>=2个

            or_count = sum(1 for x in treeNode.children if x.name == "或")
            and_count = sum(1 for x in treeNode.children if x.name == "与")
            if and_count > 1 or or_count > 1:
                use_number_or = True

            if use_number_or:
                return_str += useSubOrMoudle(return_str, treeNode, level,maxDepth, index)
                # return_str += f"以下{numToChinese(len(treeNode.children))}类子工况任意一类发生\n"
                # for item in treeNode.children:
                #     child_str = getResultFromChild(item, level + 1, maxDepth,False)[0]
                #     if len(child_str) ==0:
                #         continue
                #     return_str += f"{num_to_circle(index + 1)}"
                #
                #     if not (check_last_punct(child_str)):
                #         if index == len(treeNode.children) - 1:
                #             child_str += "，"
                #         elif index >= 0:
                #             child_str += "、"
                #
                #     return_str += child_str
                #     return_str += "\n"
                #     index = index + 1
                # return_str += "上述情况任意一种出现"
            else:
                # 或的分支有两个，并且没有其他语言符号，并且主语相同则主语合并，谓语相同则谓语合并

                canMerge = True
                child_str_list = []
                domain_str = ''
                range_str = ''
                same_domain = True
                same_range = True
                for item in treeNode.children:
                    if item.type == 0:
                        if item.name == "或" or item.name == "与" or item.name == "N取M":
                            canMerge = False
                            break
                    # 得到主语，谓语
                    child_str_listitem = getResultFromChild(item, level + 1, maxDepth, False)
                    child_str_list.append(child_str_listitem)
                    if len(domain_str) == 0:
                        domain_str = child_str_listitem[1]
                        range_str = child_str_listitem[2]
                        if "或" in range_str:
                            canMerge = False
                            break
                    else:
                        if child_str_listitem[1] != domain_str:
                            same_domain = False
                        if child_str_listitem[2] != range_str:
                            same_range = False

                if canMerge:
                    if same_domain and same_range:
                        canMerge = False
                    else:
                        if same_domain or same_range:
                            # 主和谓语至少有一个相同
                            if same_domain:
                                return [f"{domain_str}{child_str_list[0][2]}或{child_str_list[1][2]}", "", ""]
                            else:
                                return [f"{child_str_list[0][1]}或{child_str_list[1][1]}{range_str}", "", ""]
                        else:
                            canMerge = False
                # 判断是否包含或
                contain_or = False
                for item in treeNode.children:
                    child_str = getResultFromChild(item, level + 1, maxDepth, False)[0]
                    if "或" in child_str:
                        contain_or = True
                        break
                if contain_or:
                    return_str += useSubOrMoudle(return_str, treeNode, level,maxDepth, index)
                else:
                    for item in treeNode.children:
                        child_str = getResultFromChild(item, level + 1, maxDepth, False)[0]
                        if index >= 1:
                            return_str += "、"

                        return_str +=  strip_end_punctuation(child_str)
                        index = index + 1
                    return_str += "任意一种情况出现"
            return [return_str, "", ""]
        elif treeNode.name == "绝对值":
            child = treeNode.children[0]
            child_str = getResultFromChild(child, level, maxDepth, False)[0]
            return [f"{child_str}的绝对值", child_str, "的绝对值"]
        elif treeNode.name == "报警阈":
            # return_str = ""
            if len(treeNode.children) > 0 and 'sustainMinute' in treeNode.valueDic and 'compare' in treeNode.valueDic:
                child = treeNode.children[0]
                child_str = getResultFromChild(child, level, maxDepth, False)[0]
                value = int(treeNode.valueDic['operateParameter'])
                return [f"{child_str}持续{treeNode.valueDic['sustainMinute']}分钟{treeNode.valueDic['compare']}{value}",child_str, f"持续{treeNode.valueDic['sustainMinute']}分钟{treeNode.valueDic['compare']}{value}"]
            else:
                return ["", "", ""]
        else:
            print(f"error 3: {treeNode.name}")
    print(f"return 空")
    return ["", "", ""]

def getChildren(pid, treeNode):
    t_cyper1 = f"MATCH (m:Fault)-[r:CHILD_NODE_FAULT]->(n) where id(n)={pid} return m, id(m) as id_m, labels(m) as labels, r.status as status, r.weight as weight, r.operateType as operateType, r.durationMinutes as durationMinutes"
    results = run_cypher(t_cyper1)
    for res in results:
        m = res["m"]
        id_m = res["id_m"]
        labels = res["labels"]
        status = res["status"]
        weight = res["weight"]
        if "FaultOperator" in labels:
            if 'name' not in m:
                # print("error1")
                return ["", "", ""]
            item_treeNode = DefectTreeNode(m['name'], m, 0, status= status)
            treeNode.add_child(item_treeNode)
            getChildren(id_m, item_treeNode)
            item_treeNode.set_parent(treeNode)
            item_treeNode.set_weight(weight)
        else:

            shadow_cyper1 = f"MATCH(n) -[r: REFERENCE_SHADOW]->(m) where id(n)={id_m} return m, id(m) as id_m"
            shadow_results = run_cypher(shadow_cyper1)
            for res in shadow_results:
                m = res["m"]
                id_m = res["id_m"]
                item_treeNode = DefectTreeNode(m['名称'], m, 1, status= status)
                treeNode.add_child(item_treeNode)
                item_treeNode.set_parent(treeNode)
                if weight is not None:
                    item_treeNode.set_weight(weight)


# queryAllDefectsMode()
# df = pd.DataFrame(columns=["id", "名称", "描述"])
# parseDefectById(89256,'', "中压级电气各母线变压器电气参数异常", df)

node = parseDefectTreeById(0,'TL011TL131D0Q1UP051GQLY00001')
print(node)

# 50111
# 89039
# 144427



# 273730

# 417012
# A引风机叶轮结垢或磨损
# AND(nofm(2,2), nofm(2,2))