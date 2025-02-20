
import wget
import os

def url_to_file(url: str, filename: str) -> str:

    # data_file = tempfile.NamedTemporaryFile(prefix="web_data_", suffix=".txt", delete=False).name
    if not os.path.isfile(filename):
        wget.download(url, out=filename)

    return filename
