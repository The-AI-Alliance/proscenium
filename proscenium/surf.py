
import httpx
from pydantic.networks import HttpUrl
from pathlib import Path

async def url_to_file(url: HttpUrl, file_path: Path):

    async with httpx.AsyncClient() as client:

        response = await client.get(url)
        response.raise_for_status()

        with open(file_path, "wb") as file:
            file.write(response.content)
