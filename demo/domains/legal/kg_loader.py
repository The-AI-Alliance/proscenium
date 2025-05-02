from typing import Optional, Callable

import logging
from pathlib import Path
from rich.console import Console
from neo4j import GraphDatabase

from proscenium.scripts.knowledge_graph import load_knowledge_graph

from demo.domains.legal.doc_enricher import LegalOpinionEnrichments

log = logging.getLogger(__name__)


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


def make_kg_loader(
    input: Path,
    neo4j_uri: str,
    neo4j_username: str,
    neo4j_password: str,
    console: Optional[Console] = None,
) -> Callable[[bool], None]:

    def load(force: bool = False):

        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))

        num_nodes = 0
        with driver.session() as session:
            num_nodes = session.run("MATCH (n) RETURN COUNT(n) AS cnt").single().value()

        if num_nodes > 0 and not force:
            log.info(
                "Knowledge graph already exists at %s and has at least one node. Skipping its load.",
                neo4j_uri,
            )
            driver.close()
            return

        load_knowledge_graph(
            driver,
            input,
            LegalOpinionEnrichments,
            doc_enrichments_to_graph,
        )

        driver.close()

    return load
