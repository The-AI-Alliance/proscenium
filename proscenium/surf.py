
import httpx
from pydantic.networks import HttpUrl
from pathlib import Path

async def url_to_file(url: HttpUrl, data_file: Path, overwrite: bool = False):

    if data_file.exists() and not overwrite:
        # print(f"File {data_file} exists. Use overwrite=True to replace.")
        return

    async with httpx.AsyncClient() as client:

        # print(f"Downloading {url} to {data_file}...")
        response = await client.get(url)
        response.raise_for_status()

        with open(data_file, "wb") as file:
            file.write(response.content)
