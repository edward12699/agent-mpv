"""
Week 1 / Day 3：Document → Chunk → Embedding

目标：搞懂 RAG 数据准备阶段，不接 Agent / Vector Store。
"""

# from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings


DEMO_DIR = Path(__file__).resolve().parent
DATA_PATH = DEMO_DIR / "data" / "contracts.txt"
EMBEDDING_MODEL = "text-embedding-v3"


def load_document(path: Path) -> Document:
    text = path.read_text(encoding="utf-8")
    return Document(
        page_content=text,
        metadata={"source": str(path)},
    )


def split_into_chunks(
    document: Document,
    *,
    chunk_size: int,
    chunk_overlap: int = 30,
) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_documents([document])
    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = index
        chunk.metadata["chunk_size"] = chunk_size
        chunk.metadata["chunk_overlap"] = chunk_overlap
    return chunks


def print_chunks(chunks: list[Document], title: str) -> None:
    print("\n" + "#" * 60)
    print(title)
    print("#" * 60)
    print(f"共 {len(chunks)} 个 chunk")
    for chunk in chunks:
        print("=" * 50)
        print("chunk:", chunk.metadata["chunk_id"])
        print(chunk.page_content)
        print("metadata:", chunk.metadata)


def create_embeddings() -> OpenAIEmbeddings:
    """
    百炼兼容模式的 embedding 需要：
    1. 使用 dashscope compatible-mode base_url
    2. check_embedding_ctx_length=False
       （否则会先用 tiktoken 转成 token id，百炼会报 contents 参数错误）
    """
    settings = get_settings()
    # 环境里若设置了 OPENAI_BASE_URL（如 chatanywhere），settings.base_url 会覆盖百炼地址。
    # Day 3 的 text-embedding-v3 走百炼官方兼容接口更稳妥。
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


def experiment_a_chunk_sizes(document: Document) -> list[Document]:
    """实验 A：对比不同 chunk_size 的切分效果。"""
    working_chunks: list[Document] = []
    for chunk_size in (50, 200, 500):
        chunks = split_into_chunks(
            document,
            chunk_size=chunk_size,
            chunk_overlap=30,
        )
        print_chunks(
            chunks,
            title=f"实验 A：chunk_size={chunk_size}, chunk_overlap=30",
        )
        if chunk_size == 200:
            working_chunks = chunks
    return working_chunks


def experiment_b_query_embeddings(embeddings: OpenAIEmbeddings) -> None:
    """实验 B：观察语义接近的问题 vs 无关问题的向量。"""
    queries = [
        "合同违约金是多少？",
        "解除合同要赔多少钱？",
        "今天天气怎么样？",
    ]
    print("\n" + "#" * 60)
    print("实验 B：Query Embedding（语义向量）")
    print("#" * 60)
    for query in queries:
        vector = embeddings.embed_query(query)
        print("-" * 50)
        print("query:", query)
        print("type:", type(vector))
        print("dim:", len(vector))
        print("preview:", [round(x, 6) for x in vector[:10]])


def embed_chunks(
    embeddings: OpenAIEmbeddings,
    chunks: list[Document],
) -> None:
    texts = [chunk.page_content for chunk in chunks]
    vectors = embeddings.embed_documents(texts)
    print("\n" + "#" * 60)
    print("Document Embedding（chunk_size=200）")
    print("#" * 60)
    print("chunks:", len(chunks))
    print("vectors:", len(vectors))
    print("vector_dim:", len(vectors[0]) if vectors else 0)
    # zip 把「第 i 个文本块」和「第 i 个向量」配对
    for index, (chunk, vector) in enumerate(zip(chunks, vectors)):
        print("-" * 50)
        print("chunk_id:", index)
        print("metadata:", chunk.metadata)
        print("content_preview:", chunk.page_content[:60].replace("\n", " "))
        print("vector_preview:", [round(x, 6) for x in vector[:5]])


def main() -> None:
    print("原始文档路径:", DATA_PATH)
    document = load_document(DATA_PATH)
    print("\n" + "#" * 60)
    print("1 个大 Document")
    print("#" * 60)
    print(document)
    print("metadata:", document.metadata)
    print("page_content 长度:", len(document.page_content))

    working_chunks = experiment_a_chunk_sizes(document)

    embeddings = create_embeddings()
    embed_chunks(embeddings, working_chunks)
    experiment_b_query_embeddings(embeddings)

    print("\n" + "#" * 60)
    print("Day 3 完成：Document → Chunk → Embedding")
    print("明天 Day 4：Vector Store + Retriever")
    print("#" * 60)


if __name__ == "__main__":
    main()
