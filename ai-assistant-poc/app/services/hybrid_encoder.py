import openai
from langsmith import traceable
from langsmith.wrappers import wrap_openai
from pinecone_text.sparse import BM25Encoder
from app.core.config import settings

# Initialize default pre-trained BM25 Encoder
bm25 = BM25Encoder.default()
client = wrap_openai(openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY))

class HybridEncoder:
    @staticmethod
    @traceable(name="HybridEncoder.get_dense_embedding", run_type="embedding")
    async def get_dense_embedding(text: str) -> list[float]:
        response = await client.embeddings.create(
            input=text,
            model=settings.EMBEDDING_MODEL
        )
        return response.data[0].embedding

    @staticmethod
    @traceable(name="HybridEncoder.get_sparse_embedding", run_type="embedding")
    def get_sparse_embedding(text: str) -> dict:
        sparse_dict = bm25.encode_documents([text])[0] if isinstance(text, list) else bm25.encode_queries(text)
        return {
            "indices": sparse_dict["indices"],
            "values": sparse_dict["values"]
        }

    @staticmethod
    @traceable(name="HybridEncoder.convex_scale")
    def convex_scale(dense_vec: list[float], sparse_vec: dict, alpha: float = 0.5):
        """Alpha: 1.0 = Pure Dense, 0.0 = Pure Sparse (BM25)"""
        scaled_dense = [val * alpha for val in dense_vec]
        scaled_sparse = {
            "indices": sparse_vec["indices"],
            "values": [val * (1.0 - alpha) for val in sparse_vec["values"]]
        }
        return scaled_dense, scaled_sparse