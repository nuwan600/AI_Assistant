import re
from fastapi import HTTPException, status
from langsmith import traceable

# Prompt Injection Attack Patterns
INJECTION_PATTERNS = [
    r"ignore (all )?previous instructions",
    r"system prompt",
    r"you are now an unrestricted",
    r"bypass authorization",
    r"reveal (all )?passwords",
    r"dump database",
    r"sudo ",
    r"eval\(",
]

class GuardrailService:
    @staticmethod
    @traceable(name="GuardrailService.validate_user_input", run_type="parser")
    def validate_user_input(query: str) -> str:
        """Checks for common prompt injection patterns and sanitizes inputs."""
        cleaned_query = query.strip()
        
        if not cleaned_query:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Input prompt cannot be empty."
            )
            
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, cleaned_query, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Security Guardrail Triggered: Potential prompt injection or unauthorized instruction override detected."
                )
                
        return cleaned_query

    @staticmethod
    @traceable(name="GuardrailService.validate_output_citations", run_type="parser")
    def validate_output_citations(response_text: str, available_docs: list[dict]) -> str:
        """Prevents hallucinated citations by verifying returned document IDs against retrieved contexts."""
        valid_doc_ids = {doc.get("document_id") for doc in available_docs if doc.get("document_id")}
        
        # Extract citations like [doc_001]
        cited_ids = set(re.findall(r"\[(doc_\d+)\]", response_text))
        
        hallucinated = cited_ids - valid_doc_ids
        if hallucinated:
            # Append guardrail warning disclaimer if hallucinated citations are present
            response_text += f"\n\n*(Guardrail Note: The citation(s) {list(hallucinated)} could not be verified against official retrieved records.)*"
            
        return response_text