"""
Week 1 / Day 5：Basic RAG

目标：Question → Retriever → Context → Prompt → LLM → Answer
今天手写完整 RAG，不接 Agent，不用 create_retrieval_chain。
"""

from pathlib import Path
import shutil

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.agent_langchain import create_default_chat_model
from app.core.config import get_settings


DEMO_DIR = Path(__file__).resolve().parent
DATA_PATH = DEMO_DIR / "data" / "contracts.txt"
PERSIST_DIR = DEMO_DIR / "chroma_db"
EMBEDDING_MODEL = "text-embedding-v3"
COLLECTION_NAME = "contracts"

TEST_QUESTIONS = [
    "解除合同需要赔多少钱？",
    "2024年的合同金额是多少？",
    "付款方式是什么？",
    "哪家公司和杭州B公司签过合同？",
    "这家公司CEO是谁？",
]


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
    if PERSIST_DIR.exists():
        shutil.rmtree(PERSIST_DIR)

    return Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(PERSIST_DIR),
    )


def build_retriever(vector_store: Chroma):
    return vector_store.as_retriever(
        search_kwargs={"k": 3},
    )


def retrieve_context(retriever, question: str) -> list[Document]:
    return retriever.invoke(question)


def build_context(docs: list[Document]) -> str:
    parts = []
    for index, doc in enumerate(docs):
        source = doc.metadata.get("source", "unknown")
        chunk_id = doc.metadata.get("chunk_id", "unknown")
        parts.append(
            f"""[来源 {index + 1}]
source: {source}
chunk_id: {chunk_id}

{doc.page_content}"""
        )
    return "\n\n".join(parts)


def build_prompt(question: str, context: str) -> str:
    return f"""你是合同分析助手。

请严格根据提供的上下文回答。

规则：
1. 不允许使用上下文之外的信息
2. 如果上下文中没有答案，回答“根据当前资料无法确定”
3. 回答时注明使用了哪个来源，例如：[来源1]、[来源2]

上下文：
{context}

用户问题：
{question}
"""


def answer_with_rag(
    llm: ChatOpenAI,
    retriever,
    question: str,
) -> tuple[list[Document], str, str]:
    docs = retrieve_context(retriever, question)
    context = build_context(docs)
    prompt = build_prompt(question, context)
    response = llm.invoke([HumanMessage(content=prompt)])
    answer = response.content if isinstance(response.content, str) else str(response.content)
    return docs, context, answer


def print_rag_result(
    question: str,
    docs: list[Document],
    context: str,
    answer: str,
) -> None:
    print("\n" + "#" * 60)
    print("Question:", question)
    print("#" * 60)

    print("\n--- Retriever 返回 ---")
    if not docs:
        print("(空)")
    for index, doc in enumerate(docs):
        preview = doc.page_content[:100].replace("\n", " ")
        print(
            f"[{index + 1}] chunk_id={doc.metadata.get('chunk_id')} | {preview}"
        )

    print("\n--- Context ---")
    print(context)

    print("\n--- LLM Answer ---")
    print(answer)

    print("\n--- 排错提示 ---")
    print("先看 Retriever 是否召回正确 chunk（Retrieval）")
    print("再看 LLM 是否正确使用这些 chunk（Generation）")


def main() -> None:
    settings = get_settings()
    document = load_document(DATA_PATH)
    chunks = build_chunks(document)
    embeddings = create_embeddings()
    vector_store = build_vector_store(chunks, embeddings)
    retriever = build_retriever(vector_store)
    llm = create_default_chat_model(settings)

    print("Day 5 Basic RAG")
    print("文档:", DATA_PATH)
    print("chunks:", len(chunks))
    print("model:", settings.agent_model)

    for question in TEST_QUESTIONS:
        docs, context, answer = answer_with_rag(llm, retriever, question)
        print_rag_result(question, docs, context, answer)

    print("\n" + "#" * 60)
    print("Day 5 完成：Basic RAG")
    print("明天 Day 6：把 Retriever 包装成 Tool，接回 Agent")
    print("#" * 60)


if __name__ == "__main__":
    main()
