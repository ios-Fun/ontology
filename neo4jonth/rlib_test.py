# rdflib的测试方法，测试AnnotationProperty使用

from rdflib import OWL, RDF, RDFS, XSD, Graph, Namespace, URIRef, Literal, BNode

# Create a new RDF graph
g = Graph()

# Define namespaces
# Use a generic namespace for the ontology
base_ns = Namespace("http://voc.neo4j.com/datamodel#")
g.bind("", base_ns)
g.bind("owl", OWL)
g.bind("rdfs", RDFS)
g.bind("xsd", XSD)

# Create the ontology declaration
ontology_uri = URIRef("http://voc.neo4j.com/datamodel")
g.add((ontology_uri, RDF.type, OWL.Ontology))

class_uri = base_ns["Person"]
g.add((class_uri, RDF.type, OWL.Class))


g.add((class_uri, RDFS.label,
           Literal("机组")))

# 增加一个注释类型
match_confidence = base_ns["matchConfidence"]
g.add((match_confidence, RDF.type, OWL.AnnotationProperty))
g.add((match_confidence, RDFS.label, Literal("matchConfidence")))

g.add((class_uri, RDFS.label, Literal("机组#1炉冷再至辅汽电动门")))

g.add((class_uri, match_confidence, Literal("1111222")))



prop_uri1 = base_ns["属性1"]
g.add((prop_uri1, RDF.type, OWL.DatatypeProperty))

prop_uri2 = base_ns["属性2"]
g.add((prop_uri2, RDF.type, OWL.DatatypeProperty))

restriction_class1 = BNode()
g.add((restriction_class1, RDF.type, OWL.Restriction))
g.add((restriction_class1, OWL.onProperty, prop_uri1))

restriction_class2 = BNode()
g.add((restriction_class2, RDF.type, OWL.Restriction))
g.add((restriction_class2, OWL.onProperty, prop_uri2))

g.add((class_uri, RDFS.subClassOf, restriction_class1))
g.add((restriction_class1, OWL.hasValue, Literal("333")))

g.add((class_uri, RDFS.subClassOf, restriction_class2))
g.add((restriction_class2, OWL.hasValue, Literal("444")))

result_str = g.serialize(format="turtle")

with open('example3.ttl', 'w', encoding="utf-8") as f:
    f.write(result_str)