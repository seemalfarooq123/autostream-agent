from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import FakeEmbeddings


def create_vectorstore():
    loader = TextLoader("knowledge.txt")
    docs = loader.load()

    embeddings = FakeEmbeddings(size=1536)
    db = FAISS.from_documents(docs, embeddings)

    return db


def retrieve_answer(query, db):
    docs = db.similarity_search(query, k=2)

    if not docs:
        return "Sorry, I couldn't find relevant information."

    context = "\n".join([doc.page_content for doc in docs])

    return f"Here’s what I found:\n{context}"