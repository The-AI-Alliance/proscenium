
from typing import List

import nltk
nltk.download('punkt')
nltk.download('punkt_tab')

def documents_to_chunks(
    filename: str,
    min_chunk_size: int = 1000,
    # TODO chunk_overlap
    ) -> List[str]:

    chunks = []
    with open(filename, 'r') as f:
        text = f.read()
        sentences = nltk.sent_tokenize(text)
        chunk = ""
        for sentence in sentences:
            if len(chunk) < min_chunk_size:
                if len(chunk) > 0:
                    chunk += " "
                chunk += sentence
            else:
                chunks.append(chunk)
                chunk = sentence

        chunks.append(chunk)


    return chunks
