from proscenium.scripts.entity_resolver import Resolver

default_embedding_model_id = "all-MiniLM-L6-v2"

case_resolver = Resolver(
    "MATCH (cr:CaseRef) RETURN cr.text AS text",
    "text",
    "resolve_caserefs",
)

judge_resolver = Resolver(
    "MATCH (jr:JudgeRef) RETURN jr.text AS text",
    "text",
    "resolve_judgerefs",
)

resolvers = [case_resolver, judge_resolver]
