from openai import OpenAI
from llama_index.readers.file import PDFReader
from llama_index.core.node_parser import SentenceSplitter
from dotenv import load_dotenv
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

load_dotenv()

# client = OpenAI()
MODEL = "llama3.2"
client = Ollama(model=MODEL)

# Chunk it is mean break pdf down into smaller pieces, and then embed those smaller pieces
# Open ai if use api key
# EMBED_MODEL = "text-embedding-3-large"
# EMED_DIM = 3072

# using ollama
EMBED_MODEL = "nomic-embed-text"
embed_model = OllamaEmbedding(model_name=EMBED_MODEL)

# chunk_overlap mean to split sentence to chunk
# Example: hello my name is Tom -> it will get my name is Tom
splitter = SentenceSplitter(chunk_size=1000, chunk_overlap=200)

def load_and_chunk_pdf(path: str):
    docs = PDFReader().load_data(file=path)
    texts = [d.text for d in docs if getattr(d, "text", None)]
    chunks = []
    for t in texts:
        chunks.extend(splitter.split_text(t))

    return chunks


# Generate embeddings using a local ollama model
def embed_texts(texts: list[str]) -> list[list[float]]:
    return embed_model.get_text_embedding_batch(texts)

# this function use for open ai key
# def embed_texts(texts: list[str]) -> list[list[float]]:
#     response = client.embeddings.create(
#         model = EMBED_MODEL,
#         input = texts,
#     )

#     return [item.embedding for item in response.data]