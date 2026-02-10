import re

def validate_answer(answer: str, passages: list[str]) -> bool:
    if not answer or "provided documentation" in answer:
        return True  # allow refusal string
    # Require at least one [n] citation and limit hallucinated section headers
    if not re.search(r"\[\d+\]", answer):
        return False
    # Optional: very light check that citations refer to available range
    max_n = len(passages)
    for m in re.finditer(r"\[(\d+)\]", answer):
        n = int(m.group(1))
        if n < 1 or n > max_n:
            return False
    return True
