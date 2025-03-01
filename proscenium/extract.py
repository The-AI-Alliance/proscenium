
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

def get_triples_from_extract(extract, case_name, categories):
    triples = []
    lines = extract.splitlines()
    for line in lines:
        try:
            # Take the number off of the front.
            line = line.split(". ", 1)[1]
            role, entity = line.split(": ", 2)
            if role in categories:
                triple = (entity, role, case_name)
                triples.append(triple)
        except (ValueError, IndexError):
            print(f"Error parsing case {id} line: {line}")
    return triples
