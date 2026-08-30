from pinecone import Pinecone
from langsmith import traceable
from app.core.config import settings
from app.services.hybrid_encoder import HybridEncoder
from app.models.schema import UserRole

pc = None
_index = None

def get_index():
    global pc, _index
    if _index is None:
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        _index = pc.Index(settings.PINECONE_INDEX_NAME)
    return _index

class RetrievalService:
    @staticmethod
    @traceable(name="RetrievalService.hybrid_search", run_type="retriever")
    async def hybrid_search(
        query: str,
        user_role: UserRole,
        department: str = None,
        doc_type: str = None,
        top_k: int = 5,
        alpha: float = 0.5
    ) -> list[dict]:
        
        # 1. Generate Query Encodings
        dense_vector = await HybridEncoder.get_dense_embedding(query)
        sparse_vector = HybridEncoder.get_sparse_embedding(query)
        
        # 2. Scale Hybrid Weights
        scaled_dense, scaled_sparse = HybridEncoder.convex_scale(dense_vector, sparse_vector, alpha=alpha)

        # 3. RBAC & Filter Rules
        # Viewers can only view 'public' and 'internal' access_levels
        allowed_access = ["public", "internal"]
        if user_role in [UserRole.ANALYST, UserRole.ADMINISTRATOR]:
            allowed_access.append("confidential")

        filter_dict = {
            "access_level": {"$in": allowed_access}
        }
        if department:
            filter_dict["department"] = {"$eq": department}
        if doc_type:
            filter_dict["document_type"] = {"$eq": doc_type}

        # 4. Async Query Execution on Pinecone Namespace
        response = get_index().query(
            namespace="enterprise_docs",
            vector=scaled_dense,
            sparse_vector=scaled_sparse,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict
        )

        # 5. Format Documents
        results = []
        for match in response.matches:
            results.append({
                "id": match.id,
                "score": match.score,
                "text": match.metadata.get("text"),
                "document_id": match.metadata.get("document_id"),
                "title": match.metadata.get("title"),
                "department": match.metadata.get("department"),
                "access_level": match.metadata.get("access_level"),
                "created_date": match.metadata.get("created_date")
            })

        return results