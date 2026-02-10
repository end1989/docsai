DOCS_ONLY_SYSTEM = """You are a meticulous documentation expert.
You MUST answer only using the provided passages.
- If an answer is not supported, reply exactly: "Not found in the provided documentation."
- Always include bracket citations [1], [2], ... that map to the provided passages.
- Prefer exact parameter names, defaults, code blocks, and headings as quoted evidence.
- Be concise and technical. Do not invent details beyond the passages."""

def build_prompt(question: str, passages: list[str]):
    # Create a numbered citation table the model can reference.
    cites = []
    for i, p in enumerate(passages, 1):
        # Trim long passages to keep the prompt efficient
        text = p.strip()
        if len(text) > 1500:
            text = text[:1500] + " ..."
        cites.append(f"[{i}] {text}")
    cite_block = "\n".join(cites) if cites else "[1] No passages provided."
    return f"""{DOCS_ONLY_SYSTEM}

Question:
{question}

Relevant Passages:
{cite_block}

Instructions:
- Answer using ONLY the Relevant Passages.
- Cite like [1], [2] for each factual assertion.
- If not supported: "Not found in the provided documentation."
Answer:"""
