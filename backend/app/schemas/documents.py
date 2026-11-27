from datetime import datetime

from pydantic import BaseModel


# One document of the knowledge base, built from its rows in the chunks table
class DocumentOut(BaseModel):
    name: str            # the file name it was loaded from (chunks.source)
    chunks: int          # how many pieces it was cut into
    added: datetime      # when it was last loaded (re-running the ingest script replaces its rows)
    size_bytes: int      # total text in its chunks; about the file size (long sections overlap a little)
