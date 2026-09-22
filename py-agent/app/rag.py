"""合同文档向量检索。给 search_documents 工具使用。"""

from functools import lru_cache
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .core.config import get_settings


CONTRACTS_PATH = (
    Path(__file__).resolve().parents[1] / "embedding-demo" / "data" / "contracts.txt"
)
PERSIST_DIR = Path(__file__).resolve().parents[1] / "embedding-demo" / "chroma_db"
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


@lru_cache
def get_retriever():
    embeddings = create_embeddings()
    if not PERSIST_DIR.exists():
        chunks = load_chunks()
        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            collection_name=COLLECTION_NAME,
            persist_directory=str(PERSIST_DIR),
        )
    else:
        vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=str(PERSIST_DIR),
        )
    return vector_store.as_retriever(search_kwargs={"k": 3})
