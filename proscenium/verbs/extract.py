from string import Formatter


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
