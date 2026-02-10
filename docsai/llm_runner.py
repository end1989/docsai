import subprocess, tempfile, textwrap, shlex, requests, json
from .guards.prompts import build_prompt

def _run_with_ollama(cfg, question, passages):
    model = cfg["model"]["llm"]["ollama_model"]
    n_ctx = int(cfg["model"]["llm"].get("n_ctx", 256000))
    temperature = float(cfg["model"]["llm"].get("temperature", 0.2))
    top_p = float(cfg["model"]["llm"].get("top_p", 0.9))

    prompt = build_prompt(question, passages)
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_ctx": n_ctx,
            "temperature": temperature,
            "top_p": top_p
        }
    }
    r = requests.post("http://127.0.0.1:11434/api/generate", json=payload, timeout=600)
    r.raise_for_status()
    data = r.json()
    out = (data.get("response") or "").strip()
    if "Answer:" in out:
        out = out.split("Answer:", 1)[1].strip()
    return out

def _run_with_llamacpp(cfg, question, passages):
    model = cfg["model"]["llm"]["path"]
    llama_bin = cfg["model"]["llm"]["llama_binary"]
    n_ctx = cfg["model"]["llm"].get("n_ctx", 120000)

    prompt = build_prompt(question, passages)
    # Write prompt to a temp file to avoid cmdline escaping mess
    import tempfile
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as f:
        f.write(prompt)
        prompt_path = f.name

    cmd = f"{shlex.quote(llama_bin)} -m {shlex.quote(model)} -n 512 -c {n_ctx} --temp 0.2 --top-p 0.9 -f {shlex.quote(prompt_path)}"
    try:
        out = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT, encoding="utf-8")
    except subprocess.CalledProcessError as e:
        out = e.output or "LLM error"
    if "Answer:" in out:
        out = out.split("Answer:", 1)[1].strip()
    return out.strip()

def run_llm(cfg, question: str, passages: list[str]) -> str:
    mode = cfg["model"]["llm"].get("mode", "llamacpp").lower()
    if mode == "ollama":
        return _run_with_ollama(cfg, question, passages)
    return _run_with_llamacpp(cfg, question, passages)
