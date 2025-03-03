
# Note: Contains potentially generic application patterns that could live in Proscenium itself.
# But they are probably still a bit brittle.

import csv
from langchain_core.documents.base import Document

from proscenium.chunk import documents_to_chunks_by_tokens
from proscenium.parse import get_triples_from_extract
from proscenium.complete import complete_simple

def process_document_chunks(
    model_id: str,
    extraction_template: str,
    predicates: dict[str, str],
    doc: Document,
    object: str,
    writer: csv.writer
    ) -> None:

    chunks = documents_to_chunks_by_tokens([doc], chunk_size=1000, chunk_overlap=0)
    for i, chunk in enumerate(chunks):

        print("chunk", i+1, "of", len(chunks))

        extract = complete_simple(
            model_id,
            "You are an entity extractor",
            extraction_template.format(text = chunk.page_content))

        new_triples = get_triples_from_extract(extract, object, predicates)

        print("   extracted", len(new_triples), "triples")
        writer.writerows(new_triples)
