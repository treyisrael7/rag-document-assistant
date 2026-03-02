"""Grounded Q&A: retrieval + LLM with citation markers."""

from openai import OpenAI

from app.core.config import settings
from app.services.jd_sections import normalize_jd_text

# Chunks are list of {chunk_id, page_number, snippet, ...}
# Returns (answer, citations)
def generate_grounded_answer(
    question: str,
    chunks: list[dict],
    max_tokens: int | None = None,
) -> tuple[str, list[dict]]:
    """
    Call OpenAI chat completion with retrieved excerpts.
    Instructs model to only use provided text, cite with [pN-cM], say when insufficient.
    """
    max_tokens = max_tokens or settings.max_completion_tokens

    if not chunks:
        return (
            "I don't have enough information in this document to answer that.",
            [],
        )

    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not configured")

    # Build excerpts with citation markers [p{page}-c{idx}]; normalize mojibake (ΓÇó→•)
    excerpt_lines = []
    for i, c in enumerate(chunks, start=1):
        page = c.get("page_number", 0)
        marker = f"[p{page}-c{i}]"
        snippet = normalize_jd_text(c.get("snippet", "")).strip()
        excerpt_lines.append(f"{marker} {snippet}")

    excerpts_text = "\n\n".join(excerpt_lines)

    system_prompt = """You are a precise Q&A assistant. You must:
1. Answer ONLY using the provided document excerpts below.
2. If the excerpts do not contain sufficient evidence to answer the question, say so clearly (e.g., "The document does not contain enough information to answer this.").
3. Include citation markers like [p3-c2] in your answer wherever you cite a specific excerpt. Use the exact marker format from the excerpts.
4. Be concise. Do not add information not present in the excerpts."""

    user_content = f"""Document excerpts:
{excerpts_text}

Question: {question}

Answer (cite with [pN-cM] markers when using an excerpt):"""

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        max_tokens=max_tokens,
    )

    answer = (response.choices[0].message.content or "").strip()

    citations = [
        {
            "chunk_id": c["chunk_id"],
            "page_number": c["page_number"],
            "snippet": normalize_jd_text(c.get("snippet", "")),
        }
        for c in chunks
    ]

    return answer, citations
