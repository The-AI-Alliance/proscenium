
import logging

from typing import List

extraction_template = """\
Below is a list of entity categories:

{categories}

Given this list of entity categories, you will be asked to extract entities belonging to these categories from a text passage.
Consider only the list of entity categories above; do not extract any additional entities.
For each entity found, list the category and the entity, separated by a semicolon.
Do not use the words "Entity" or "Category".

Find the entities in the following text, and list them in the format specified above:

{text}
"""

def get_triples_from_extract(extract, case_name, categories) -> List[tuple[str, str, str]]:
    logging.info("get_triples_from_extract: extract = <<<%s>>>", extract)
    triples = []
    lines = extract.splitlines()
    for line in lines:
        try:
            #line = line.split(". ", 1)[1] # for numbered list
            role, entity = line.split("; ", 2)
            #role_lower = role.lower()
            #if "not explicitly mentioned" not in r and "not applicable" not in r and "not specified" not in r:
            if role in categories:
                triple = (entity.strip(), role, case_name)
                triples.append(triple)
            else:
                logging.warning("Skipping line <<<%s>>> due to unknown role: %s", line, role)
        except (ValueError, IndexError):
            logging.error("Error parsing line <<<%s>>>", line)
    return triples
