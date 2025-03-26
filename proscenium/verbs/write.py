from typing import List

import csv


def triples_to_csv(triples: List[tuple[str, str, str]], filename: str) -> None:

    with open(filename, "wt") as f:
        writer = csv.writer(f, delimiter=",", quotechar='"')
        writer.writerow(["entity", "role", "case name"])  # header
        writer.writerows(triples)
