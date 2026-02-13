from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio
from app.audit.audit_state import get_state

router = APIRouter()

subscribers = set()

async def event_stream():
    queue = asyncio.Queue()
    subscribers.add(queue)
    try:
        while True:
            data = await queue.get()
            yield f"data: {data}\n\n"
    finally:
        subscribers.remove(queue)


@router.get("/subscribe")
async def subscribe():
    return StreamingResponse(event_stream(), media_type="text/event-stream")


def broadcast(message: str):
    for q in list(subscribers):
        q.put_nowait(message)