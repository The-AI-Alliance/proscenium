from rich import print
from rich.panel import Panel

from langchain_core.documents.base import Document

case_template = """
[u]{name}[/u]
{reporter}, Volume {volume}
Pages {first_page}-{last_page}
Court: {court}
Decision Date: {decision_date}
Citations: {citations}

Docket Number: {docket_number}
Jurisdiction: {jurisdiction}
Judges: {judges}
Parties: {parties}

Last Updated: {last_updated}
Provenance: {provenance}
Word Count: {word_count}, Char Count: {char_count}
Id: {id}
""" # leaves out head_matter

def display_case(doc: Document):
    case_str = case_template.format_map(doc.metadata)
    print(Panel(case_str, title=doc.metadata['name_abbreviation']))
