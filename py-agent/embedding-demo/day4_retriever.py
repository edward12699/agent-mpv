"""
Week 1 / Day 4：Vector Store + Retriever

目标：把 chunk 写入向量库，按用户问题召回 Top-K。
今天只做到 Retrieval，不接 LLM / Agent。
"""

from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings


DEMO_DIR = Path(__file__).resolve().parent
DATA_PATH = DEMO_DIR / "data" / "contracts.txt"
PERSIST_DIR = DEMO_DIR / "chroma_db"
EMBEDDING_MODEL = "text-embedding-v3"
COLLECTION_NAME = "contracts"


def load_document(path: Path) -> Document:
    text = path.read_text(encoding="utf-8")
    return Document(
        page_content=text,
        metadata={"source": str(path)},
    )


def build_chunks(document: Document) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=30,
    )
    chunks = splitter.split_documents([document])
    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = index
    return chunks


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


def build_vector_store(
    chunks: list[Document],
    embeddings: OpenAIEmbeddings,
) -> Chroma:
    # 每次重建本地 collection，避免重复写入旧数据干扰实验
    if PERSIST_DIR.exists():
        import shutil

        shutil.rmtree(PERSIST_DIR)

    return Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(PERSIST_DIR),
    )


def demo_similarity_search(vector_store: Chroma) -> None:
    query = "解除合同需要赔多少钱？"
    print("\n" + "#" * 60)
    print("similarity_search")
    print("query:", query)
    print("#" * 60)

    results = vector_store.similarity_search(query, k=3)
    for index, doc in enumerate(results):
        print("=" * 50)
        print("rank:", index + 1)
        print(doc.page_content)
        print(doc.metadata)


def demo_similarity_search_with_score(vector_store: Chroma) -> None:
    query = "解除合同需要赔多少钱？"
    print("\n" + "#" * 60)
    print("similarity_search_with_score")
    print("query:", query)
    print("注意：Chroma 这里的 score 通常是距离，越小越相似")
    print("#" * 60)

    results = vector_store.similarity_search_with_score(query, k=3)
    for doc, score in results:
        print("=" * 50)
        print("score:", score)
        print(doc.page_content)
        print(doc.metadata)


def demo_retriever(vector_store: Chroma) -> None:
    retriever = vector_store.as_retriever(
        search_kwargs={"k": 3},
    )
    query = "违约责任是什么？"
    print("\n" + "#" * 60)
    print("retriever.invoke")
    print("query:", query)
    print("#" * 60)

    docs = retriever.invoke(query)
    for index, doc in enumerate(docs):
        print("=" * 50)
        print("rank:", index + 1)
        print(doc.page_content)
        print(doc.metadata)


def experiment_four_queries(vector_store: Chroma) -> None:
    """实验：相关问题 vs 无关问题。"""
    retriever = vector_store.as_retriever(
        search_kwargs={"k": 3},
    )
    queries = [
        "解除合同需要赔多少钱？",
        "合同付款方式是什么？",
        "2024年的合同金额是多少？",
        "今天天气怎么样？",
    ]

    print("\n" + "#" * 60)
    print("实验：4 个 query（默认 Top-K，无关问题也会硬返回）")
    print("#" * 60)

    for query in queries:
        docs = retriever.invoke(query)
        print("\n" + "=" * 50)
        print("query:", query)
        print(f"returned: {len(docs)} docs")
        for index, doc in enumerate(docs):
            preview = doc.page_content[:80].replace("\n", " ")
            print(f"  [{index + 1}] chunk_id={doc.metadata.get('chunk_id')} | {preview}")


def experiment_score_threshold(vector_store: Chroma) -> None:
    """
    用 similarity_score_threshold 过滤弱相关结果。
    LangChain 会把距离转成 relevance score（通常越大越相关），
    threshold 需要按实际分数分布调，不能拍脑袋。
    """
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": 3,
            "score_threshold": 0.5,
        },
    )
    queries = [
        "解除合同需要赔多少钱？",
        "今天天气怎么样？",
    ]

    print("\n" + "#" * 60)
    print("实验：score_threshold=0.5")
    print("#" * 60)

    for query in queries:
        docs = retriever.invoke(query)
        print("\n" + "=" * 50)
        print("query:", query)
        print(f"returned: {len(docs)} docs")
        if not docs:
            print("  []  ← 无关问题被过滤（理想情况）")
            continue
        for index, doc in enumerate(docs):
            preview = doc.page_content[:80].replace("\n", " ")
            print(f"  [{index + 1}] chunk_id={doc.metadata.get('chunk_id')} | {preview}")


def main() -> None:
    print("原始文档路径:", DATA_PATH)
    document = load_document(DATA_PATH)
    chunks = build_chunks(document)
    print(f"chunks: {len(chunks)}")
    for chunk in chunks:
        print("-" * 40)
        print("chunk_id:", chunk.metadata["chunk_id"])
        print(chunk.page_content[:80].replace("\n", " "))

    embeddings = create_embeddings()
    vector_store = build_vector_store(chunks, embeddings)
    print("\nVector Store 已写入 Chroma")
    print("persist_directory:", PERSIST_DIR)
    print("collection:", COLLECTION_NAME)

    demo_similarity_search(vector_store)
    demo_similarity_search_with_score(vector_store)
    demo_retriever(vector_store)
    experiment_four_queries(vector_store)
    experiment_score_threshold(vector_store)

    print("\n" + "#" * 60)
    print("Day 4 完成：Vector Store + Retriever")
    print("关键结论：最相似 ≠ 真相关")
    print("明天 Day 5：Basic RAG（Retriever → Prompt → LLM）")
    print("#" * 60)


if __name__ == "__main__":
    main()
