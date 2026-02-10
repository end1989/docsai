# --- top of file ---
from bs4 import BeautifulSoup
import hashlib, re, orjson, requests, markdownify
import time
from urllib.parse import urljoin, urlparse
import urllib.robotparser as robotparser
from pathlib import Path
from typing import List, Dict, Tuple
from ..file_parsers import FileParser, scan_directory

ZERO_WIDTH = re.compile(r"[\u200B\u200C\u200D\u2060]")

HEADERS = {
    "User-Agent": "DocsAI/0.1 (+local; respectful crawler)"
}

def _hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()

def _clean_html(html: str) -> BeautifulSoup:
    soup = BeautifulSoup(html, "lxml")
    # Nuke non-content
    for tag in soup.find_all(["script","style","template","svg","noscript","link","meta"]):
        tag.decompose()
    # Prefer main/article when available
    root = soup.select_one("main") or soup.select_one("article") or soup.body or soup
    return root

def _html_to_md(html: str) -> str:
    root = _clean_html(html)
    md = markdownify.markdownify(str(root), heading_style="ATX")
    md = ZERO_WIDTH.sub("", md)                  # strip zero-widths
    md = re.sub(r"\n{3,}", "\n\n", md)           # squeeze blank lines
    md = re.sub(r"[ \t]{2,}", " ", md)           # squeeze spaces
    # Drop obvious leftover CSS blocks if any leaked
    if re.search(r"--s-|\.sn-|{ ?--", md):
        md = "\n".join(
            ln for ln in md.splitlines()
            if not re.search(r"--[a-zA-Z0-9-]+:|^\s*@|^\s*\.[a-zA-Z0-9_-]+\s*{", ln)
        )
    return md.strip()

def _chunk(md: str, tok=800, overlap=120) -> List[str]:
    words = md.split()
    if len(words) < 50:
        return []
    out, i = [], 0
    step = max(tok - overlap, 1)
    while i < len(words):
        out.append(" ".join(words[i:i+tok]))
        i += step
    return out
_robots_cache: dict[str, robotparser.RobotFileParser | None] = {}

def _robots_allowed(start_domain: str, url: str, respect: bool) -> bool:
    if not respect:
        return True
    parsed = urlparse(start_domain)
    domain_key = f"{parsed.scheme}://{parsed.netloc}"

    if domain_key not in _robots_cache:
        robots_url = f"{domain_key}/robots.txt"
        print(f"[ROBOTS] Fetching {robots_url}")
        try:
            r = requests.get(robots_url, headers=HEADERS, timeout=10)
            if r.status_code == 200 and "text/html" not in r.headers.get("Content-Type", ""):
                rp = robotparser.RobotFileParser()
                rp.parse(r.text.splitlines())
                _robots_cache[domain_key] = rp
                print(f"[ROBOTS] Parsed robots.txt for {domain_key}")
            else:
                # 403/404/HTML response — no valid robots.txt, allow all
                _robots_cache[domain_key] = None
                print(f"[ROBOTS] No valid robots.txt for {domain_key} (status={r.status_code}), allowing all")
        except Exception as e:
            _robots_cache[domain_key] = None
            print(f"[ROBOTS] Error fetching robots.txt for {domain_key}: {e}, allowing all")

    rp = _robots_cache[domain_key]
    if rp is None:
        return True
    allowed = rp.can_fetch(HEADERS["User-Agent"], url)
    if not allowed:
        print(f"[ROBOTS] Blocked by robots.txt: {url}")
    return allowed

def _is_allowed_path(url: str, start_domain: str, allowed_paths: list[str]) -> bool:
    # Stay on same host + within at least one allowed prefix
    u = urlparse(url)
    d = urlparse(start_domain)
    if u.netloc != d.netloc:
        return False
    if not allowed_paths:
        return True
    path = u.path or "/"
    return any(path.startswith(p) for p in allowed_paths)

def _read_cache(cache_dir: Path, url: str) -> str | None:
    h = hashlib.sha1(url.encode("utf-8")).hexdigest() + ".html"
    p = cache_dir / h
    if p.exists():
        try:
            return p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None
    return None

def _write_cache(cache_dir: Path, url: str, html: str) -> None:
    h = hashlib.sha1(url.encode("utf-8")).hexdigest() + ".html"
    p = cache_dir / h
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        p.write_text(html, encoding="utf-8")
    except Exception:
        pass

def crawl_website(start_url: str, allowed_paths: list[str], max_depth: int, cache_dir: Path, on_page=None) -> dict[str, str]:
    """
    Tiny, respectful BFS crawler with caching.
    Returns dict[url] = html
    on_page: optional callback(url, page_count) called after each page is fetched
    """
    # Extract base domain from start_url for path checking
    parsed_start = urlparse(start_url)
    base_domain = f"{parsed_start.scheme}://{parsed_start.netloc}"

    print(f"[CRAWL] Starting crawl of {start_url}")
    print(f"[CRAWL] Base domain: {base_domain}")
    print(f"[CRAWL] Allowed paths: {allowed_paths}")
    print(f"[CRAWL] Max depth: {max_depth}")
    print(f"[CRAWL] Cache dir: {cache_dir}")

    seen: set[str] = set()
    out: dict[str, str] = {}

    # BFS frontier: list of (url, depth)
    frontier: list[tuple[str, int]] = [(start_url, 0)]

    while frontier:
        url, depth = frontier.pop(0)
        if url in seen:
            continue
        seen.add(url)

        print(f"[CRAWL] Checking URL: {url} (depth: {depth})")

        if not _is_allowed_path(url, base_domain, allowed_paths):
            print(f"[CRAWL] Skipping {url} - not in allowed paths")
            continue
        if not _robots_allowed(base_domain, url, respect=True):
            print(f"[CRAWL] Skipping {url} - blocked by robots.txt")
            continue

        # load cached or fetch
        html = _read_cache(cache_dir, url)
        if html is None:
            print(f"[CRAWL] Fetching {url} (not in cache)")
            try:
                r = requests.get(url, headers=HEADERS, timeout=20)
                print(f"[CRAWL] Response status: {r.status_code}, Content-Type: {r.headers.get('Content-Type', 'unknown')}")
                if r.status_code != 200 or "text/html" not in (r.headers.get("Content-Type","")):
                    print(f"[CRAWL] Skipping {url} - bad status or not HTML")
                    continue
                html = r.text
                _write_cache(cache_dir, url, html)
                print(f"[CRAWL] Cached {url}")
                # be courteous
                time.sleep(0.3)
            except Exception as e:
                print(f"[CRAWL] Error fetching {url}: {e}")
                continue
        else:
            print(f"[CRAWL] Using cached version of {url}")

        out[url] = html
        print(f"[CRAWL] Added {url} to output (total: {len(out)})")
        if on_page:
            on_page(url, len(out))

        if depth >= max_depth:
            print(f"[CRAWL] Reached max depth for {url}")
            continue

        # discover links
        try:
            soup = BeautifulSoup(html, "lxml")
            links_found = 0
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
                    continue
                nxt = urljoin(url, href)
                # keep within same domain + allowed paths
                if _is_allowed_path(nxt, base_domain, allowed_paths):
                    frontier.append((nxt, depth + 1))
                    links_found += 1
            print(f"[CRAWL] Found {links_found} valid links on {url}")
        except Exception as e:
            print(f"[CRAWL] Error parsing links from {url}: {e}")
            pass

    print(f"[CRAWL] Crawl complete. Found {len(out)} pages.")
    return out

def ingest_profile(profile_name: str, cfg: Dict, paths: Dict):
    typ = cfg["source"]["type"]
    import chromadb
    from chromadb.config import Settings
    client = chromadb.Client(Settings(is_persistent=True, persist_directory=str(paths["chroma"])))
    coll = client.get_or_create_collection(name="docs")

    docs: List[Tuple[str, str, Dict]] = []

    if typ == "web" or typ == "mixed":
        domain = cfg["source"]["domain"].rstrip("/")
        allowed = cfg["source"].get("allowed_paths", [])
        depth = int(cfg["source"].get("depth", 2))

        # If we have allowed paths, start crawling from those paths
        # Otherwise start from the domain root
        if allowed:
            # Start crawling from each allowed path
            raw = {}
            for path in allowed:
                start_url = domain + path
                print(f"[INGEST] Starting crawl from: {start_url}")
                crawl_results = crawl_website(start_url, allowed, depth, paths["cache"])
                raw.update(crawl_results)
        else:
            raw = crawl_website(domain, allowed, depth, paths["cache"])
        for url, html in raw.items():
            md = _html_to_md(html)
            if not md or len(md) < 100:
                continue
            chunks = _chunk(md, cfg["ingest"]["chunk_tokens"], cfg["ingest"]["chunk_overlap"])
            if not chunks:
                continue
            url_hash = _hash(url)
            for idx, chunk in enumerate(chunks):
                if len(chunk) < cfg["ingest"]["min_text_len"]:
                    continue
                # UNIQUE per upsert call (and stable across runs)
                cid = f"{url_hash}_{idx}_{_hash(chunk)[:8]}"
                text = f"{chunk}\n\n(Source: {url})"
                metadata = {"source_url": url, "chunk_index": idx, "source_type": "web"}
                docs.append((cid, text, metadata))

    if typ == "local" or typ == "mixed":
        # Handle local file ingestion
        local_paths = cfg["source"].get("local_paths", [])
        file_types = cfg["source"].get("file_types", ['all'])

        print(f"[INGEST] Processing local directories: {local_paths}")
        print(f"[INGEST] File types: {file_types}")

        parser = FileParser()

        for local_path in local_paths:
            path = Path(local_path)
            if not path.exists():
                print(f"[INGEST] Warning: Path does not exist: {local_path}")
                continue

            if path.is_file():
                # Single file
                files = [str(path)]
            else:
                # Directory - scan for files
                files = scan_directory(str(path), file_types, recursive=True)

            print(f"[INGEST] Found {len(files)} files in {local_path}")

            for filepath in files:
                print(f"[INGEST] Processing: {filepath}")
                result = parser.parse_file(filepath)

                if result and result.get('content'):
                    content = result['content']
                    file_metadata = result['metadata']

                    # Skip very short files
                    if len(content) < 100:
                        continue

                    # Chunk the content
                    chunks = _chunk(content, cfg["ingest"]["chunk_tokens"], cfg["ingest"]["chunk_overlap"])
                    if not chunks:
                        continue

                    file_hash = _hash(filepath)
                    for idx, chunk in enumerate(chunks):
                        if len(chunk) < cfg["ingest"]["min_text_len"]:
                            continue

                        # Create unique ID
                        cid = f"{file_hash}_{idx}_{_hash(chunk)[:8]}"

                        # Add source info to text
                        text = f"{chunk}\n\n(Source: {file_metadata['filename']})"

                        # Create metadata
                        metadata = {
                            "source_path": filepath,
                            "filename": file_metadata['filename'],
                            "chunk_index": idx,
                            "source_type": "local",
                            "file_type": file_metadata['extension'],
                            "modified": file_metadata['modified']
                        }

                        docs.append((cid, text, metadata))
                else:
                    print(f"[INGEST] Failed to parse: {filepath} - {result.get('error', 'Unknown error')}")

    elif typ == "openapi":
        files = cfg["source"]["files"]
        md_map = load_openapi(files)
        for url, md in md_map.items():
            chunks = _chunk(md, cfg["ingest"]["chunk_tokens"], cfg["ingest"]["chunk_overlap"])
            url_hash = _hash(url)
            for idx, chunk in enumerate(chunks):
                if len(chunk) < cfg["ingest"]["min_text_len"]:
                    continue
                cid = f"{url_hash}_{idx}_{_hash(chunk)[:8]}"
                text = f"{chunk}\n\n(Source: {url})"
                metadata = {"source_url": url, "chunk_index": idx}
                docs.append((cid, text, metadata))
    elif typ not in ("web", "local", "mixed", "openapi"):
        raise ValueError(f"Unknown source type: {typ}")

    if not docs:
        print("No documents to index.")
        return

    # Ensure IDs are unique within this batch (paranoia)
    seen = set()
    dedup_ids, dedup_texts, dedup_metadatas = [], [], []
    for cid, txt, metadata in docs:
        if cid in seen:  # should not happen now, but guard anyway
            continue
        seen.add(cid)
        dedup_ids.append(cid)
        dedup_texts.append(txt)
        dedup_metadatas.append(metadata)

    coll.upsert(ids=dedup_ids, documents=dedup_texts, metadatas=dedup_metadatas)
    print(f"Ingested {len(dedup_ids)} chunks into {paths['chroma']}")
