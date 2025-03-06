
import logging

from typing import List, Dict

from string import Formatter

class PartialFormatter(Formatter):
    def get_value(self, key, args, kwargs):
        try:
            return super().get_value(key, args, kwargs)
        except KeyError:
            return "{" + key + "}"

raw_extraction_template = """\
Below is a list of entity categories:

{predicates}

Given this list of entity categories, you will be asked to extract entities belonging to these categories from a text passage.
Consider only the list of entity categories above; do not extract any additional entities.
For each entity found, list the category and the entity, separated by a semicolon.
Do not use the words "Entity" or "Category".

Find the entities in the following text, and list them in the format specified above:

{text}
"""

def get_triples_from_extract(
    extract,
    object: str,
    predicates: Dict[str, str]
    ) -> List[tuple[str, str, str]]:

    logging.info("get_triples_from_extract: extract = <<<%s>>>", extract)

    triples = []
    lines = extract.splitlines()
    for line in lines:
        try:
            #line = line.split(". ", 1)[1] # for numbered list
            predicate, subject = line.split("; ", 2)
            #role_lower = role.lower()
            #if "not explicitly mentioned" not in r and "not applicable" not in r and "not specified" not in r:
            if predicate in predicates:
                triple = (subject.strip(), predicate, object)
                triples.append(triple)
            else:
                logging.warning("Skipping line <<<%s>>> due to unknown role: %s", line, predicate)
        except (ValueError, IndexError):
            logging.error("Error parsing line <<<%s>>>", line)
    return triples
