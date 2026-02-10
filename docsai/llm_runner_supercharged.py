import subprocess, tempfile, textwrap, shlex, requests, json
from .guards.prompts_supercharged import build_prompt, build_supercharged_prompt

def _run_with_ollama(cfg, question, passages, supercharged=True, prompt_mode=None):
    """
    Run LLM with Ollama API

    Args:
        cfg: Configuration dict
        question: User's question
        passages: Retrieved passages
        supercharged: Use supercharged prompts (default: True)
        prompt_mode: Specific prompt mode ('comprehensive', 'integration', 'debugging', 'learning')
    """
    model = cfg["model"]["llm"]["ollama_model"]
    n_ctx = int(cfg["model"]["llm"].get("n_ctx", 256000))

    # Adjust temperature based on mode
    if supercharged and prompt_mode in ["debugging", "integration"]:
        # Lower temperature for technical accuracy
        temperature = float(cfg["model"]["llm"].get("temperature", 0.1))
    else:
        temperature = float(cfg["model"]["llm"].get("temperature", 0.2))

    top_p = float(cfg["model"]["llm"].get("top_p", 0.9))

    # Build the appropriate prompt
    if supercharged and prompt_mode:
        prompt = build_supercharged_prompt(question, passages, mode=prompt_mode)
    else:
        prompt = build_prompt(question, passages, supercharged=supercharged)

    # For supercharged mode, request more tokens for comprehensive responses
    max_tokens = 2048 if supercharged else 512

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_ctx": n_ctx,
            "temperature": temperature,
            "top_p": top_p,
            "num_predict": max_tokens,  # Allow longer responses
            "stop": None  # Don't cut off responses
        }
    }

    # Longer timeout for comprehensive responses
    timeout = 900 if supercharged else 600

    try:
        r = requests.post("http://127.0.0.1:11434/api/generate", json=payload, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        out = (data.get("response") or "").strip()

        # Clean up response based on mode
        if supercharged:
            # For supercharged, look for the response section
            if "YOUR COMPREHENSIVE RESPONSE:" in out:
                out = out.split("YOUR COMPREHENSIVE RESPONSE:", 1)[1].strip()
            elif "Answer:" in out:
                out = out.split("Answer:", 1)[1].strip()
        else:
            # Original parsing for basic mode
            if "Answer:" in out:
                out = out.split("Answer:", 1)[1].strip()

        return out

    except requests.exceptions.Timeout:
        return "Request timed out. The question may require a simpler query or the model may be overloaded."
    except requests.exceptions.RequestException as e:
        print(f"Ollama API error: {e}")
        return "Error connecting to the LLM. Please ensure Ollama is running."

def _run_with_llamacpp(cfg, question, passages, supercharged=True, prompt_mode=None):
    """
    Run LLM with llama.cpp binary

    Args:
        cfg: Configuration dict
        question: User's question
        passages: Retrieved passages
        supercharged: Use supercharged prompts (default: True)
        prompt_mode: Specific prompt mode
    """
    model = cfg["model"]["llm"]["path"]
    llama_bin = cfg["model"]["llm"]["llama_binary"]
    n_ctx = cfg["model"]["llm"].get("n_ctx", 120000)

    # Build the appropriate prompt
    if supercharged and prompt_mode:
        prompt = build_supercharged_prompt(question, passages, mode=prompt_mode)
    else:
        prompt = build_prompt(question, passages, supercharged=supercharged)

    # Write prompt to a temp file to avoid cmdline escaping mess
    import tempfile
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as f:
        f.write(prompt)
        prompt_path = f.name

    # More tokens for comprehensive responses
    n_predict = 2048 if supercharged else 512
    temp = 0.1 if prompt_mode in ["debugging", "integration"] else 0.2

    cmd = f"{shlex.quote(llama_bin)} -m {shlex.quote(model)} -n {n_predict} -c {n_ctx} --temp {temp} --top-p 0.9 -f {shlex.quote(prompt_path)}"

    try:
        out = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT, encoding="utf-8")
    except subprocess.CalledProcessError as e:
        out = e.output or "LLM error"

    # Clean up response
    if supercharged:
        if "YOUR COMPREHENSIVE RESPONSE:" in out:
            out = out.split("YOUR COMPREHENSIVE RESPONSE:", 1)[1].strip()
        elif "Answer:" in out:
            out = out.split("Answer:", 1)[1].strip()
    else:
        if "Answer:" in out:
            out = out.split("Answer:", 1)[1].strip()

    return out.strip()

def detect_prompt_mode(question: str) -> str:
    """
    Automatically detect the best prompt mode based on the question

    Returns:
        One of: 'comprehensive', 'integration', 'debugging', 'learning'
    """
    question_lower = question.lower()

    # Integration patterns
    if any(word in question_lower for word in [
        "implement", "integrate", "build", "create", "setup", "configure",
        "workflow", "architecture", "design", "develop", "deploy"
    ]):
        return "integration"

    # Debugging patterns
    if any(word in question_lower for word in [
        "error", "fail", "issue", "problem", "fix", "debug", "wrong",
        "not working", "broken", "troubleshoot", "solve"
    ]):
        return "debugging"

    # Learning patterns
    if any(word in question_lower for word in [
        "what is", "what are", "how does", "how do", "explain",
        "understand", "learn", "why", "when", "difference between"
    ]):
        return "learning"

    # Default to comprehensive
    return "comprehensive"

def run_llm(cfg, question: str, passages: list[str], supercharged: bool = None, prompt_mode: str = None) -> str:
    """
    Run the LLM with the given question and passages

    Args:
        cfg: Configuration dictionary
        question: User's question
        passages: List of relevant passages from the knowledge base
        supercharged: Whether to use supercharged prompts (default: from config or True)
        prompt_mode: Override prompt mode ('comprehensive', 'integration', 'debugging', 'learning')

    Returns:
        The LLM's response as a string
    """
    # Check config for supercharged setting, default to True
    if supercharged is None:
        supercharged = cfg.get("model", {}).get("llm", {}).get("supercharged", True)

    # Auto-detect prompt mode if not specified
    if prompt_mode is None and supercharged:
        prompt_mode = detect_prompt_mode(question)
        print(f"[LLM] Using {prompt_mode} mode for this question")

    mode = cfg["model"]["llm"].get("mode", "llamacpp").lower()

    if mode == "ollama":
        return _run_with_ollama(cfg, question, passages, supercharged, prompt_mode)
    else:
        return _run_with_llamacpp(cfg, question, passages, supercharged, prompt_mode)

# Enhanced response post-processing
def enhance_response_formatting(response: str) -> str:
    """
    Enhance the formatting of the response for better readability

    This is especially useful for supercharged responses that may be longer
    """
    # Ensure proper spacing around headers
    response = response.replace("\n#", "\n\n#")
    response = response.replace("#", "\n#")

    # Ensure proper spacing around code blocks
    response = response.replace("```", "\n```")
    response = response.replace("```\n\n", "```\n")

    # Clean up excessive newlines
    while "\n\n\n" in response:
        response = response.replace("\n\n\n", "\n\n")

    return response.strip()

# Backwards compatible wrapper
def run_llm_basic(cfg, question: str, passages: list[str]) -> str:
    """
    Backwards compatible function using original restrictive prompts
    """
    return run_llm(cfg, question, passages, supercharged=False)