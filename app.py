from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from langchain.vectorstores import Chroma
from langchain.storage import InMemoryStore
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain.schema import Document
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from base64 import b64decode
import uvicorn

# ==== LangChain RAG Setup ====
embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = Chroma(collection_name="multi_modal_rag", embedding_function=embedding_function)
store = InMemoryStore()
id_key = "doc_id"

retriever = MultiVectorRetriever(
    vectorstore=vectorstore,
    docstore=store,
    id_key=id_key,
)

# Helper to parse documents
def parse_docs(docs):
    b64, text = [], []
    for doc in docs:
        try:
            # Try if it's base64 (assume image)
            b64decode(doc.page_content)
            b64.append(doc.page_content)
        except:
            # Assume it's text-based document
            if isinstance(doc, Document):
                text.append(doc)
            else:
                text.append(Document(page_content=str(doc)))
    return {"images": b64, "texts": text}

# Build prompt for multi-modal input
def build_prompt(kwargs):
    docs_by_type = kwargs["context"]
    user_question = kwargs["question"]

    # Extract text content safely
    context_text = "\n".join([doc.page_content for doc in docs_by_type["texts"]])

    prompt_template = f"""
Answer the question based only on the following context (text, tables, images).

Context:
{context_text}

Question:
{user_question}
"""
    prompt_content = [{"type": "text", "text": prompt_template.strip()}]

    for image in docs_by_type["images"]:
        prompt_content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image}"},
            }
        )

    return [HumanMessage(content=prompt_content)]

# Define RAG pipeline
rag_chain = (
    {
        "context": RunnableLambda(lambda x: x["question"]) | retriever | RunnableLambda(parse_docs),
        "question": RunnablePassthrough(),
    }
    | RunnableLambda(build_prompt)
    | ChatOllama(model="llava:7b", temperature=0.4)
    | StrOutputParser()
)

# ==== FastAPI Setup ====
app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ganti dengan asal frontend kalau perlu
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str

@app.post("/ask/")
async def ask_rag(request: QueryRequest):
    try:
        input_data = {"question": request.question}
        print("Invoking with:", input_data)  # Tambahkan ini
        answer = rag_chain.invoke(input_data)
        print("Answer:", answer)  # Tambahkan ini
        return {"question": request.question, "answer": answer}
    except Exception as e:
        import traceback
        print("Exception in /ask:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "Multimodal RAG API is running!"}

@app.options("/ask/")
async def options():
    return {}
