import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import datetime

from database import db, create_document, get_documents

app = FastAPI(title="Shahbaz AI Backend", description="BlueFlame Intelligence core API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Models -----
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    mode: Optional[Literal[
        "qa", "writing", "translation", "summary", "student", "professional", "fun"
    ]] = "qa"
    language: Optional[Literal["en", "ur", "hi"]] = "en"

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    suggestions: List[str]
    mode: str
    created_at: str

class ImageRequest(BaseModel):
    prompt: str
    style: Optional[str] = None

# ----- Helpers (lightweight local AI to keep app fully functional without external keys) -----

def _tone_wrap(text: str, mode: str) -> str:
    if mode == "student":
        return (
            "Student Mode:\n" +
            "- Simple explanation\n- Key points\n- Short example\n\n" + text
        )
    if mode == "professional":
        return (
            "Professional Mode:\n" +
            "- Concise\n- Actionable\n- Business tone\n\n" + text
        )
    if mode == "fun":
        return (
            "Fun Mode 🎉:\n" + text + "\n(peppered with a friendly, upbeat vibe)"
        )
    return text

def _generate_reply(prompt: str, mode: str, language: str) -> str:
    base = prompt.strip()
    if mode == "translation":
        # ultra-simple glossary-like translation mock
        translations = {
            "hello": {"ur": "سلام", "hi": "नमस्ते"},
            "how are you": {"ur": "آپ کیسے ہیں", "hi": "आप कैसे हैं"},
        }
        key = base.lower()
        if key in translations and language in translations[key]:
            return f"Translation ({language}): {translations[key][language]}"
        return f"Translation ({language}): {base}"
    if mode == "summary":
        words = base.split()
        if len(words) > 40:
            summary = " ".join(words[:40]) + "…"
        else:
            summary = base
        return f"Summary: {summary}"
    if mode == "writing":
        return (
            "Here is a polished draft based on your request:\n\n"
            f"Title: {base[:60]}\n\n"
            "Paragraph 1: A clear introduction that frames the goal and context.\n\n"
            "Paragraph 2: Key insights, structure, and supporting details with a smooth narrative.\n\n"
            "Paragraph 3: A succinct wrap‑up with next steps and a strong closing."
        )
    # default Q&A style
    answer = (
        "Answer: "
        f"{base}\n\n"
        "Key points:\n- Direct answer\n- Extra context\n- Practical tip"
    )
    return answer


def _smart_suggestions(mode: str) -> List[str]:
    bank = {
        "qa": ["Explain in simple terms", "Give key takeaways", "Add examples"],
        "writing": ["Draft an outline", "Expand to 1000 words", "Refine tone"],
        "translation": ["Detect language", "Back-translate", "Transliterate"],
        "summary": ["Bullet summary", "TL;DR", "Action items"],
        "student": ["Create study notes", "Make quiz questions", "Explain like I'm 12"],
        "professional": ["Make an executive summary", "Draft an email", "Create a plan"],
        "fun": ["Tell a pun", "Make it playful", "Add emojis"],
    }
    return bank.get(mode or "qa", bank["qa"])[:3]

# ----- Routes -----

@app.get("/")
def root():
    return {"brand": "Shahbaz AI", "powered_by": "BlueFlame Intelligence", "status": "ok"}

@app.get("/api/modes")
def get_modes():
    return {
        "modes": [
            "qa", "writing", "translation", "summary", "student", "professional", "fun"
        ]
    }

@app.post("/api/chat")
def chat(req: ChatRequest):
    # Ensure a session record exists
    session_id = req.session_id
    if not session_id:
        from schemas import ChatSession  # local import to avoid circular
        session = ChatSession(title=f"Chat – {datetime.utcnow().strftime('%H:%M')}", mode=req.mode or "qa")
        session_id = create_document("chatsession", session)
    # Store user message
    from schemas import ChatMessage as ChatMsg
    user_msg = ChatMsg(session_id=session_id, role="user", content=req.message, mode=req.mode)
    create_document("chatmessage", user_msg)

    # Generate reply locally (no external API key required)
    core = _generate_reply(req.message, req.mode or "qa", req.language or "en")
    reply_text = _tone_wrap(core, req.mode or "qa")

    # Store assistant message
    assistant_msg = ChatMsg(session_id=session_id, role="assistant", content=reply_text, mode=req.mode)
    create_document("chatmessage", assistant_msg)

    return {
        "session_id": session_id,
        "reply": reply_text,
        "suggestions": _smart_suggestions(req.mode or "qa"),
        "mode": req.mode or "qa",
        "created_at": datetime.utcnow().isoformat(),
    }

@app.get("/api/sessions")
def list_sessions(limit: int = 50):
    try:
        docs = get_documents("chatsession", {}, limit)
        for d in docs:
            d["_id"] = str(d["_id"])  # serialize
        return {"sessions": docs}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/messages/{session_id}")
def list_messages(session_id: str, limit: int = 200):
    try:
        docs = get_documents("chatmessage", {"session_id": session_id}, limit)
        for d in docs:
            d["_id"] = str(d["_id"])  # serialize
        return {"messages": docs}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/image")
def image(req: ImageRequest):
    # Create a neon-blue SVG data URI (works offline and instantly)
    prompt = (req.prompt or "Shahbaz AI").strip()
    title = prompt[:80]
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">
    <defs>
      <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
        <stop offset="0%" stop-color="#00A8FF"/>
        <stop offset="50%" stop-color="#00EFFF"/>
        <stop offset="100%" stop-color="#64FFFF"/>
      </linearGradient>
      <filter id="glow" x="-40%" y="-40%" width="180%" height="180%">
        <feGaussianBlur stdDeviation="12" result="coloredBlur"/>
        <feMerge>
          <feMergeNode in="coloredBlur"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>
    </defs>
    <rect width="1024" height="1024" fill="#000814"/>
    <circle cx="512" cy="512" r="360" fill="url(#g)" opacity="0.15" filter="url(#glow)"/>
    <path d="M512 240 C600 260 700 340 720 460 C700 520 620 560 560 640 C520 700 520 760 512 784 C504 760 504 700 464 640 C404 560 324 520 304 460 C324 340 424 260 512 240 Z" fill="url(#g)" opacity="0.9" filter="url(#glow)"/>
    <text x="50%" y="82%" dominant-baseline="middle" text-anchor="middle" font-family="Inter, Arial" font-size="44" fill="#E6F7FF" opacity="0.95">{title}</text>
    <text x="50%" y="90%" dominant-baseline="middle" text-anchor="middle" font-family="Inter, Arial" font-size="24" fill="#8AD8FF" opacity="0.85">Shahbaz AI · BlueFlame</text>
  </svg>'''
    import base64
    data_uri = "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("utf-8")

    # store request
    try:
        from schemas import ImageRequest as ImgReq
        create_document("imagerequest", ImgReq(prompt=req.prompt, style=req.style))
    except Exception:
        pass

    return {"image": data_uri}

@app.get("/test")
def test_database():
    """Verify DB connectivity"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = os.getenv("DATABASE_NAME") or "❌ Not Set"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
