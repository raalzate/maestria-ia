from dotenv import load_dotenv
from typing import List
from temporalio import activity

from pydantic import BaseModel

load_dotenv()


class Transaction(BaseModel):
    date: str
    desc: str
    amount: float

# --- Simulación de Base de Datos ---
TRANSACTIONS_DB: List[Transaction] = [
    Transaction(date="2025-10-12", desc="Pago con tarjeta en Supermercado La Cesta", amount=-75.50),
    Transaction(date="2025-10-14", desc="Depósito de nómina mensual de ACME Corp", amount=1500.00),
    Transaction(date="2025-10-15", desc="Transferencia a cuenta de ahorros personal", amount=-200.00),
    Transaction(date="2025-10-16", desc="Compra en línea en Tienda de Electrónica", amount=-350.99),
]

@activity.defn
async def fetch_transactions(user_id: str) -> List[Transaction]:
    """Simula la obtención de transacciones."""
    return TRANSACTIONS_DB

@activity.defn
async def retrieve_context_from_transactions(transactions: List[Transaction], question: str) -> str:
    """Crea índice y recupera contexto."""

    from langchain_community.vectorstores import FAISS
    from langchain_openai import  OpenAIEmbeddings
        
    embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")
    
    activity.logger.info("Creando índice y recuperando contexto relevante...")
    documents = [f"El {t.date}, se realizó la operación '{t.desc}' por un monto de {t.amount}." for t in transactions]
    vector_store = FAISS.from_texts(documents, embedding=embeddings_model)
    retriever = vector_store.as_retriever(search_kwargs={"k": 2})
    relevant_docs = retriever.invoke(question)
    context = "\n---\n".join([doc.page_content for doc in relevant_docs])
    return context

@activity.defn
async def generate_response(context: str, question: str) -> str:
    """Llama al LLM para generar la respuesta final."""
    
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_openai import ChatOpenAI
        
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, max_tokens=250)
    activity.logger.info("Generando respuesta con el LLM...")
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "Eres un asesor financiero..."),
        ("user", "PREGUNTA DEL USUARIO:\n{question}\n\nTRANSACCIONES RELEVANTES:\n{context}\n\nRESPUESTA:")
    ])
    chain = prompt_template | llm | StrOutputParser()
    response = chain.invoke({"context": context, "question": question})
    return response