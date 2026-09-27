"""向量库封装。"""

from __future__ import annotations

from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings


CONTRACTS_PATH = (
    Path(__file__).resolve().parents[2]
    / "embedding-demo"
    / "data"
    / "contracts.txt"
)
PERSIST_DIR = (
    Path(__file__).resolve().parents[2] / "embedding-demo" / "chroma_db"
)
EMBEDDING_MODEL = "text-embedding-v3"
COLLECTION_NAME = "contracts"


def create_embeddings() -> OpenAIEmbeddings:
    settings = get_settings()
    base_url = (
        "https://dashscope.aliyuncs.com/compatible-mode/v1"
        if settings.dashscope_api_key
        else settings.base_url
    )
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=settings.api_key,
        base_url=base_url,
        check_embedding_ctx_length=False,
    )


def load_chunks(path: Path = CONTRACTS_PATH) -> list[Document]:
    document = Document(
        page_content=path.read_text(encoding="utf-8"),
        metadata={"source": str(path)},
    )
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=30,
    )
    chunks = splitter.split_documents([document])
    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = index
    return chunks


def get_or_create_vector_store(
    *,
    embeddings: OpenAIEmbeddings | None = None,
) -> Chroma:
    embeddings = embeddings or create_embeddings()
    if not PERSIST_DIR.exists():
        chunks = load_chunks()
        return Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            collection_name=COLLECTION_NAME,
            persist_directory=str(PERSIST_DIR),
        )
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(PERSIST_DIR),
    )
