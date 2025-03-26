from neo4j import GraphDatabase
from neo4j import Driver


def knowledge_graph_client(uri: str, username: str, password: str) -> Driver:

    driver = GraphDatabase.driver(uri, auth=(username, password))

    return driver
