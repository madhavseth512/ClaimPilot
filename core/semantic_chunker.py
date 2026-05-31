import os
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 500))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 50))


class SemanticChunker:
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
            length_function=len,
        )

    def chunk(self, text: str, metadata: dict = None) -> List[dict]:
        raise NotImplementedError("Implemented in Phase 3")

    def chunk_with_indices(self, text: str) -> List[str]:
        return self.splitter.split_text(text)
