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
            # Order matters — tries paragraph breaks first, then sentences,
            # then words. Never splits mid-sentence.
            separators=["\n\n", "\n", ". ", "? ", "! ", ", ", " ", ""],
            length_function=len,
        )

    def chunk(self, text: str, metadata: dict = None) -> List[dict]:
        """
        Split text into overlapping chunks.
        Each chunk is returned as:
        {
            "text": str,
            "chunk_index": int,
            "metadata": { ...passed-in metadata merged with chunk_index }
        }
        """
        if not text or not text.strip():
            return []

        raw_chunks = self.splitter.split_text(text)
        base_metadata = metadata or {}

        return [
            {
                "text": chunk,
                "chunk_index": i,
                "metadata": {**base_metadata, "chunk_index": i},
            }
            for i, chunk in enumerate(raw_chunks)
            if chunk.strip()
        ]
