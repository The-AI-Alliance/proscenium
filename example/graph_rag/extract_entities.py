
import logging
from rich import print

from proscenium.display import header

# Problem-specific configuration:
import example.graph_rag.config as config
import example.graph_rag.util as util

logging.basicConfig()
logging.getLogger().setLevel(logging.WARNING)

print(header())

util.extract_entities(
    config.hf_dataset_id,
    config.hf_dataset_column,
    config.entity_csv_file)
