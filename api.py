"""
Enterprise AI Support Platform — FastAPI Backend
Session 1 of 12
"""

import json
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from support_agent import run_ticket, stream_ticket, run_session_verification

app = FastAPI(title="Enterprise AI Support Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class TicketRequest(BaseModel):
    ticket: str


@app.post("/api/run")
def run(req: TicketRequest):
    result = run_ticket(req.ticket)
    return {
        "category":       result.get("category", ""),
        "final_response": result.get("final_response", ""),
        "is_safe":        result.get("is_safe", True),
        "pii_detected":   result.get("pii_detected", False),
        "iteration_count": result.get("iteration_count", 0),
        "raw_input":      result.get("raw_input", ""),
    }


@app.post("/api/stream")
async def stream(req: TicketRequest):
    def generate():
        for node_name, snapshot in stream_ticket(req.ticket):
            payload = json.dumps({
                "node":     node_name,
                "category": snapshot.get("category", ""),
                "response": snapshot.get("final_response", ""),
            })
            yield f"data: {payload}\n\n"
        yield "data: {\"done\": true}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/verify")
def verify():
    passed = run_session_verification()
    return {"passed": passed}


@app.get("/health")
def health():
    return {"status": "ok", "session": 1}


# Serve frontend
app.mount("/", StaticFiles(directory=".", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)