
import logging
from rich import print

from proscenium.display import header

import example.graph_rag as graph_rag

logging.basicConfig()
logging.getLogger().setLevel(logging.WARNING)

print(header())

graph_rag.extract_entities(
    graph_rag.config.hf_dataset_id,
    graph_rag.config.hf_dataset_column,
    graph_rag.config.num_docs,
    graph_rag.config.entity_csv_file,
    graph_rag.config.model_id,
    graph_rag.config.extraction_template,
    graph_rag.config.doc_as_rich,
    graph_rag.config.doc_as_object,
    graph_rag.config.doc_direct_triples,
    graph_rag.config.predicates)
