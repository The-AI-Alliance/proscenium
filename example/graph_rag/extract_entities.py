
import logging
from rich import print

from proscenium.display import header

import example.graph_rag.config as config
import example.graph_rag.util as util

logging.basicConfig()
logging.getLogger().setLevel(logging.WARNING)

print(header())

util.extract_entities(
    config.hf_dataset_id,
    config.hf_dataset_column,
    config.num_docs,
    config.entity_csv_file,
    config.model_id,
    config.extraction_template,
    config.doc_as_rich,
    config.doc_as_object,
    config.doc_direct_triples,
    config.predicates)
