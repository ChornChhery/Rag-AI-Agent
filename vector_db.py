from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

class QdrantStorage:
    def __init__(self, url="http://localhost:6333", collection="docs", dim=768):
        self.client = QdrantClient(url=url, timeout=30)
        self.collection = collection
        # if don't have folder collect create new one
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )

    # Insert and Update data
    # vectors is = dim = 3072, payloads is a real data
    def upsert(self, ids, vectors, payloads):
            # Create Point structure to database
            points = [PointStruct(id=ids[i], vector=vectors[i], payload=payloads[i]) for i in range(len(ids))]
            # Insert
            self.client.upsert(self.collection, points=points)

    # Search data
    def search(self, query_vector, top_k: int=5):
        #
        results = self.client.search(
            collection_name= self.collection,
            query_vector=query_vector,
            with_payload=True,
            limit=top_k
        )
         
        # pull db to context and sources 
        contexts = []
        sources = set()
    
        # Return data
        for i in results:
            payload = getattr(i, "payload", None) or {}
            text = payload.get("text", "")
            source = payload.get("source","")
            if text:
                 contexts.append(text)
                 sources.add(source)

        return {"contexts": contexts, "sources": list(sources)}
    
    # delete collection()
    def delete(self):
         if self.client.collection_exists(self.collection):
              self.client.delete(self.collection)

