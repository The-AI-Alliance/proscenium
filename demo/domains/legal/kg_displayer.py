from typing import Optional, Callable

from rich.console import Console
from rich.table import Table
from neo4j import GraphDatabase
from neo4j import Driver


def display_knowledge_graph(driver: Driver, console: Console) -> None:

    with driver.session() as session:

        node_types_result = session.run("MATCH (n) RETURN labels(n) AS nls")
        node_types = set()
        for record in node_types_result:
            node_types.update(record["nls"])
        ntt = Table(title="Node Types", show_lines=False)
        ntt.add_column("Type", justify="left")
        for nt in node_types:
            ntt.add_row(nt)
        console.print(ntt)

        relations_types_result = session.run("MATCH ()-[r]->() RETURN type(r) AS rel")
        relation_types = [record["rel"] for record in relations_types_result]
        unique_relations = list(set(relation_types))
        rtt = Table(title="Relationship Types", show_lines=False)
        rtt.add_column("Type", justify="left")
        for rt in unique_relations:
            rtt.add_row(rt)
        console.print(rtt)

        cases_result = session.run("MATCH (n:Case) RETURN properties(n) AS p")
        cases_table = Table(title="Cases", show_lines=False)
        cases_table.add_column("Properties", justify="left")
        for case_record in cases_result:
            cases_table.add_row(str(case_record["p"]))
        console.print(cases_table)

        judgerefs_result = session.run("MATCH (n:JudgeRef) RETURN n.text AS text")
        judgerefs_table = Table(title="JudgeRefs", show_lines=False)
        judgerefs_table.add_column("Text", justify="left")
        for judgeref_record in judgerefs_result:
            judgerefs_table.add_row(judgeref_record["text"])
        console.print(judgerefs_table)

        caserefs_result = session.run("MATCH (n:CaseRef) RETURN n.text AS text")
        caserefs_table = Table(title="CaseRefs", show_lines=False)
        caserefs_table.add_column("Text", justify="left")
        for caseref_record in caserefs_result:
            caserefs_table.add_row(caseref_record["text"])
        console.print(caserefs_table)

        georefs_result = session.run("MATCH (n:GeoRef) RETURN n.text AS text")
        georefs_table = Table(title="GeoRefs", show_lines=False)
        georefs_table.add_column("Text", justify="left")
        for georef_record in georefs_result:
            georefs_table.add_row(georef_record["text"])
        console.print(georefs_table)

        companyrefs_result = session.run("MATCH (n:CompanyRef) RETURN n.text AS text")
        companyrefs_table = Table(title="CompanyRefs", show_lines=False)
        companyrefs_table.add_column("Text", justify="left")
        for companyref_record in companyrefs_result:
            companyrefs_table.add_row(companyref_record["text"])
        console.print(companyrefs_table)


def make_kg_displayer(
    neo4j_uri: str,
    neo4j_username: str,
    neo4j_password: str,
    console: Optional[Console] = None,
) -> Callable[[bool], None]:

    def display(force: bool = False):
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
        display_knowledge_graph(driver, console)
        driver.close()

    return display
