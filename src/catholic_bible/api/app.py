from typing import Literal

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from catholic_bible import __version__

app = FastAPI(title="Catholic Bible", version=__version__)


class Health(BaseModel):
    status: Literal["ok"]
    version: str


@app.get("/health")
def health() -> Health:
    return Health(status="ok", version=__version__)


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=8000)
