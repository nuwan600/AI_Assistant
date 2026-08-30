import sys
import os
from pathlib import Path

# Add project root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import asyncio
# pyrefly: ignore [missing-import]
from pinecone import Pinecone, ServerlessSpec
# pyrefly: ignore [missing-import]
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings
from app.services.hybrid_encoder import HybridEncoder

pc = Pinecone(api_key=settings.PINECONE_API_KEY)

async def setup_and_ingest():
    index_name = settings.PINECONE_INDEX_NAME
    
    # Create Index if not exists
    existing_indexes = [idx.name for idx in pc.list_indexes()]
    if index_name not in existing_indexes:
        print(f"Creating Pinecone Index: {index_name}...")
        pc.create_index(
            name=index_name,
            dimension=settings.EMBEDDING_DIMENSION,
            metric="dotproduct",  # Dotproduct required for sparse-dense hybrid
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )

    index = pc.Index(index_name)

    with open("data/mock_documents.json", "r") as f:
        documents = json.load(f)

    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    vectors = []

    for doc in documents:
        chunks = splitter.split_text(doc["content"])
        for idx, chunk in enumerate(chunks):
            chunk_id = f"{doc['id']}_chunk_{idx}"
            
            dense_vector = await HybridEncoder.get_dense_embedding(chunk)
            sparse_vector = HybridEncoder.get_sparse_embedding(chunk)

            metadata = {
                "document_id": doc["id"],
                "title": doc["title"],
                "department": doc["department"],
                "document_type": doc["document_type"],
                "access_level": doc["access_level"],
                "created_date": doc["created_date"],
                "text": chunk
            }

            vectors.append({
                "id": chunk_id,
                "values": dense_vector,
                "sparse_values": sparse_vector,
                "metadata": metadata
            })

    # Upsert in namespace 'enterprise_docs'
    index.upsert(vectors=vectors, namespace="enterprise_docs")
    print(f"Successfully upserted {len(vectors)} chunks into namespace 'enterprise_docs'.")

if __name__ == "__main__":
    asyncio.run(setup_and_ingest())