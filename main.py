import logging
from fastapi import FastAPI
import inngest
from inngest.experimental import ai
import inngest.fast_api
from dotenv import load_dotenv
import uuid
import os
import datetime

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

load_dotenv()

inngest_client = inngest.Inngest(
    app_id="rag_app",
    logger = logging.getLogger("uvicorn"),
    is_production= False,
    serializer= inngest.PydanticSerializer()
)

#ingest server function
@inngest_client.create_function(
    fn_id="RAG: Ingest PDF",
    trigger=inngest.TriggerEvent(event="rag/ingest_pdf")
)
async def rag_ingest_pdf(ctx: inngest.Context):
    try:
        # load documents from the ./data directory
        documents = SimpleDirectoryReader("./data").load_data()

        # Initialize Ollama LLM (Locally llama3.2)
        MODEL = "llama3.2"
        llm = Ollama(model = MODEL)
        embed_model = OllamaEmbedding(model_name=MODEL)

        # Build vector index using llamaIndex
        index = VectorStoreIndex.from_documents(documents,llm=llm,embed_model=embed_model)

        # Query index
        query_engine = index.as_query_engine()
        response = query_engine.query("Summarize the uploaded documents.")

        print("Summary: ",response)

        return {
            "summary": str(response),
            "status": "PDFs indexed and processed locally using Ollama"
        }
    except Exception as e:
        print("Error:", e)
        return {
            "error": str(e),
            "status": "Failed"
        }



app = FastAPI()


inngest.fast_api.serve(app, inngest_client, [rag_ingest_pdf])
