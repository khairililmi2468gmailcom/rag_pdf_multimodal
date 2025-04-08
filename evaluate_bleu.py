import json
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from tqdm import tqdm

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

def parse_docs(docs):
    b64, text = [], []
    for doc in docs:
        try:
            b64decode(doc.page_content)
            b64.append(doc.page_content)
        except:
            text.append(doc)
    return {"images": b64, "texts": text}

def build_prompt(kwargs):
    docs_by_type = kwargs["context"]
    user_question = kwargs["question"]

    context_text = "\n".join([t.page_content for t in docs_by_type["texts"]])

    prompt_template = f"""
Answer the question based only on the following context (text, tables, images).

Context:
{context_text}

Question:
{user_question}
"""
    prompt_content = [{"type": "text", "text": prompt_template}]

    for image in docs_by_type["images"]:
        prompt_content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image}"},
            }
        )

    return [HumanMessage(content=prompt_content)]

rag_chain = (
    {
        "context": retriever | RunnableLambda(parse_docs),
        "question": RunnablePassthrough(),
    }
    | RunnableLambda(build_prompt)
    | ChatOllama(model="llava:7b", temperature=0.4)
    | StrOutputParser()
)


# ==== Load generated QA ====
with open("generated_qa.json") as f:
    data = json.load(f)

# ==== Evaluate ====
smoothie = SmoothingFunction().method4
total_bleu = 0
results = []

print("🔍 Evaluating RAG answers vs ground-truth answers using BLEU...\n")

for idx, qa in enumerate(tqdm(data)):
    question = qa["question"]
    reference = qa["answer"]

    try:
        predicted = rag_chain.invoke(question)
    except Exception as e:
        predicted = ""
        print(f"⚠️ RAG failed on Q{idx+1}: {e}")

    bleu_score = sentence_bleu(
        [reference.split()],
        predicted.split(),
        smoothing_function=smoothie,
        weights=(0.5, 0.5)
    )

    results.append({
        "question": question,
        "reference": reference,
        "prediction": predicted,
        "bleu": bleu_score
    })

    total_bleu += bleu_score

# ==== Output Summary ====
avg_bleu = total_bleu / len(results)

print(f"\n✅ Finished evaluating {len(results)} questions.")
print(f"📊 Average BLEU Score: {avg_bleu:.4f}")

# Optional: Save results
with open("evaluation_results.json", "w") as f:
    json.dump(results, f, indent=2)
