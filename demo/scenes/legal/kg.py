from typing import Optional
import logging
from enum import StrEnum

from pathlib import Path
from rich.console import Console
from rich.table import Table
from neo4j import GraphDatabase
from neo4j import Driver

from proscenium.patterns.knowledge_graph import load_knowledge_graph
from demo.scenes.legal.doc_enrichments import LegalOpinionEnrichments

from proscenium.core import Prop

log = logging.getLogger(__name__)


class NodeLabel(StrEnum):
    Case = "Case"
    CaseRef = "CaseRef"
    JudgeRef = "JudgeRef"
    Judge = "Judge"
    GeoRef = "GeoRef"
    CompanyRef = "CompanyRef"


class RelationLabel(StrEnum):
    mentions = "mentions"
    references = "references"


# TODO `ReferenceSchema` may move to `proscenium.patterns.knowledge_graph`
# depending on how much potentially resuable behavior is built around it


class ReferenceSchema:
    """
    A `ReferenceSchema` is a way of denoting the text span used to establish
    a relationship between two nodes in the knowledge graph.
    """

    # (mentioner) -> [:mentions] -> (ref)
    # (ref) -> [:references] -> (referent)

    # All fields refer to node labels
    def __init__(self, mentioners: list[str], ref_label: str, referent: str):
        self.mentioners = mentioners
        self.ref_label = ref_label
        self.referent = referent


judge_ref = ReferenceSchema(
    [NodeLabel.Case],
    NodeLabel.JudgeRef,
    NodeLabel.Judge,
)

case_ref = ReferenceSchema(
    [NodeLabel.Case],
    NodeLabel.CaseRef,
    NodeLabel.Case,
)


def doc_enrichments_to_graph(tx, enrichments: LegalOpinionEnrichments) -> None:
    """
    See https://neo4j.com/docs/cypher-manual/current/clauses/merge/ for
    Cypher semantics of MERGE.
    """

    case_name = enrichments.name

    tx.run(
        "MERGE (c:Case {"
        + "name: $case, "
        + "reporter: $reporter, volume: $volume, "
        + "first_page: $first_page, last_page: $last_page, "
        + "cited_as: $cited_as, "
        + "court: $court, decision_date: $decision_date, "
        + "docket_number: $docket_number, jurisdiction: $jurisdiction, "
        + "hf_dataset_id: $hf_dataset_id, hf_dataset_index: $hf_dataset_index"
        + "})",
        case=case_name,
        reporter=enrichments.reporter,
        volume=enrichments.volume,
        first_page=enrichments.first_page,
        last_page=enrichments.last_page,
        cited_as=enrichments.cited_as,
        court=enrichments.court,
        decision_date=enrichments.decision_date,
        docket_number=enrichments.docket_number,
        jurisdiction=enrichments.jurisdiction,
        hf_dataset_id=enrichments.hf_dataset_id,
        hf_dataset_index=enrichments.hf_dataset_index,
    )

    # Resolvable fields from the document metadata

    # TODO split multiple judges upstream
    judge = enrichments.judges
    if len(judge) > 0:
        tx.run(
            "MATCH (c:Case {name: $case}) "
            + "MERGE (c)-[:authored_by]->(:JudgeRef {text: $judge, confidence: $confidence})",
            judge=judge,
            case=case_name,
            confidence=0.9,
        )
    # TODO split into plaintiff(s) and defendant(s) upstream
    parties = enrichments.parties
    tx.run(
        "MATCH (c:Case {name: $case}) "
        + "MERGE (c)-[:involves]->(:PartyRef {name: $party, confidence: $confidence})",
        party=parties,
        case=case_name,
        confidence=0.9,
    )

    # Fields extracted from the text with LLM:

    for judgeref in enrichments.judgerefs:
        tx.run(
            "MATCH (c:Case {name: $case}) "
            + "MERGE (c)-[:mentions]->(:JudgeRef {text: $judgeref, confidence: $confidence})",
            judgeref=judgeref,
            case=case_name,
            confidence=0.6,
        )

    for caseref in enrichments.caserefs:
        tx.run(
            "MATCH (c:Case {name: $case}) "
            + "MERGE (c)-[:mentions]->(:CaseRef {text: $caseref, confidence: $confidence})",
            case=case_name,
            caseref=caseref,
            confidence=0.6,
        )

    for georef in enrichments.georefs:
        tx.run(
            "MATCH (c:Case {name: $case}) "
            + "MERGE (c)-[:mentions]->(:GeoRef {text: $georef, confidence: $confidence})",
            case=case_name,
            georef=georef,
            confidence=0.6,
        )

    for companyref in enrichments.companyrefs:
        tx.run(
            "MATCH (c:Case {name: $case}) "
            + "MERGE (c)-[:mentions]->(:CompanyRef {text: $companyref, confidence: $confidence})",
            case=case_name,
            companyref=companyref,
            confidence=0.6,
        )


class CaseLawKnowledgeGraph(Prop):
    """
    A knowledge graph for case law documents, built from enriched case law documents."""

    def __init__(
        self,
        input_path: Path,
        neo4j_uri: str,
        neo4j_username: str,
        neo4j_password: str,
        console: Optional[Console] = None,
    ) -> None:
        super().__init__(console=console)
        self.input_path = input_path
        self.neo4j_uri = neo4j_uri
        self.neo4j_username = neo4j_username
        self.neo4j_password = neo4j_password

    def already_built(self) -> bool:

        num_nodes = 0
        driver = GraphDatabase.driver(
            self.neo4j_uri, auth=(self.neo4j_username, self.neo4j_password)
        )
        try:
            with driver.session() as session:
                num_nodes = (
                    session.run("MATCH (n) RETURN COUNT(n) AS cnt").single().value()
                )
        finally:
            driver.close()

        if num_nodes > 0:
            log.info(
                "Knowledge graph already exists at %s and has at least one node. Considering it built.",
                self.neo4j_uri,
            )
            return True

        return False

    def build(self) -> None:

        driver = GraphDatabase.driver(
            self.neo4j_uri, auth=(self.neo4j_username, self.neo4j_password)
        )

        try:
            load_knowledge_graph(
                driver,
                self.input_path,
                LegalOpinionEnrichments,
                doc_enrichments_to_graph,
            )
        finally:
            driver.close()


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


class CaseLawKnowledgeGraphDisplayer(Prop):

    def __init__(
        self,
        neo4j_uri: str,
        neo4j_username: str,
        neo4j_password: str,
        console: Optional[Console] = None,
    ):
        super().__init__(console=console)
        self.neo4j_uri = neo4j_uri
        self.neo4j_username = neo4j_username
        self.neo4j_password = neo4j_password

    def build(self, force: bool = False):
        driver = GraphDatabase.driver(
            self.neo4j_uri, auth=(self.neo4j_username, self.neo4j_password)
        )
        display_knowledge_graph(driver, self.console)
        driver.close()
