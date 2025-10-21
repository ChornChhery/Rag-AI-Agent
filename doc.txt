Step Up project
1. uv init .
2. uv add fastapi inngest llama-index-core llama-index-readers-file python-dotenv qdrant-client uvicorn streamlit openai
3. uv add ollama
4. uv add llama-index-llms-ollama
5. uv pip install llama-index-embeddings-ollama
6. ollama pull nomic-embed-text
7. pip install requests




Run
1. uv run uvicorn main:app


Open New Terminal:
Run Server with Inngest
1. npx inngest-cli@latest dev -u http://127.0.0.1:8000/api/inngest


Create directory data
mkdir data
ls la data -> 6520310203.pdf



Vector Database Setup with Docker 
docker run -d --name qdrant -p 6333:6333 -v "./qdrant_storage:/qdrant/storage" qdrant/qdrant
docker start qdrant
docker ps -a


# Inngest functions
1. Triggers
2. Flow Control
3. Steps
