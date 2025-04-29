from enum import StrEnum


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


# TODO `ReferenceSchema` may move to `proscenium.scripts.knowledge_graph`
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
