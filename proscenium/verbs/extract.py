import logging
from string import Formatter

import json
from pydantic import BaseModel

from proscenium.verbs.complete import complete_simple

extraction_system_prompt = "You are an entity extractor"


class PartialFormatter(Formatter):
    def get_value(self, key, args, kwargs):
        try:
            return super().get_value(key, args, kwargs)
        except KeyError:
            return "{" + key + "}"


partial_formatter = PartialFormatter()

raw_extraction_template = """\
Below is a description of a data class for storing information extracted from text:

{extraction_description}

Find the information in the following text, and provide them in the specified JSON response format.
Only answer in JSON.:

{text}
"""


def extract_to_pydantic_model(
    extraction_model_id: str,
    extraction_template: str,
    clazz: type[BaseModel],
    text: str,
    verbose: bool = False,
) -> BaseModel:

    extract_str = complete_simple(
        extraction_model_id,
        extraction_system_prompt,
        extraction_template.format(text=text),
        response_format={
            "type": "json_object",
            "schema": clazz.model_json_schema(),
        },
        rich_output=verbose,
    )

    logging.info("complete_to_pydantic_model: extract_str = <<<%s>>>", extract_str)

    try:
        extract_dict = json.loads(extract_str)
        return clazz.model_construct(**extract_dict)
    except Exception as e:
        logging.error("complete_to_pydantic_model: Exception: %s", e)

    return None
