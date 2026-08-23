from typing import List, Dict, Any, Optional
from .ingestion import store
from .models.domain import DocumentChunk

def search_documents(query: str, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Search documents for the given query.
    Enforces source precedence and customer applicability.
    """
    query_terms = [q.lower() for q in query.replace('?', ' ').replace('.', ' ').split() if len(q) > 2]
    
    scored_chunks = []
    
    for chunk in store.document_chunks:
        # Check applicability
        if chunk.metadata.customer_applicability and chunk.metadata.customer_applicability != account_id:
            continue
            
        # Score based on simple term frequency
        score = 0
        content_lower = chunk.content.lower()
        for term in query_terms:
            if term in content_lower:
                score += content_lower.count(term)
                
        # Give a small base score to agreements so they always float up if relevant to the user
        if chunk.metadata.doc_type == "Agreement" and chunk.metadata.customer_applicability == account_id:
            score += 0.5 
                
        if score > 0:
            scored_chunks.append({
                "score": score,
                "chunk": chunk
            })
            
    # Sort primarily by authority_level (1=highest, 5=lowest), then by search score descending
    scored_chunks.sort(key=lambda x: (x["chunk"].metadata.authority_level, -x["score"]))
    
    results = []
    for sc in scored_chunks[:10]:
        results.append({
            "content": sc["chunk"].content,
            "metadata": sc["chunk"].metadata.model_dump() # Pydantic v2
        })
        
    return results
