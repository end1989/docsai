from fastapi import APIRouter

router = APIRouter()

@router.get("/crawl")
def crawl():
    return {"ok": True, "message": "stub crawl"}

@router.get("/search")
def search(q: str):
    return {"ok": True, "query": q, "results": []}

@router.get("/get")
def get(id: str):
    return {"ok": True, "id": id, "text": "stub text"}
