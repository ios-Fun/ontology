from mcp_neo4j_data_modeling.data_model import DataModel, Node, Property, Relationship

def test_data_model_to_owl_turtle_str():
    """Test converting a data model to an OWL Turtle string."""
    nodes = [
        Node(
            label="Person",
            key_property=Property(
                name="personId", type="STRING", description="Unique identifier"
            ),
            properties=[
                Property(name="name", type="STRING", description="Name of the person"),
                Property(name="birthYear", type="INTEGER", description="Birth year"),
            ],
        ),
        Node(
            label="Address",
            key_property=Property(
                name="addressId", type="STRING", description="Unique identifier"
            ),
            properties=[
                Property(
                    name="streetAddress", type="STRING", description="Street address"
                ),
            ],
        ),
    ]
    relationships = [
        Relationship(
            type="LIVES_AT",
            start_node_label="Person",
            end_node_label="Address",
            properties=[],
        ),
    ]

    data_model = DataModel(nodes=nodes, relationships=relationships)
    turtle_str = data_model.to_owl_turtle_str()
    with open('example2.ttl', 'w', encoding="utf-8") as f:
        f.write(turtle_str)
    # driver.close()

test_data_model_to_owl_turtle_str()