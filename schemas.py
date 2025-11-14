"""
Database Schemas for Shahbaz AI

Each Pydantic model corresponds to a MongoDB collection using the class name in lowercase.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal

class ChatSession(BaseModel):
    """Represents a chat session metadata"""
    title: str = Field(..., description="Short title for the session")
    mode: Literal["qa", "writing", "translation", "summary", "student", "professional", "fun"] = Field(
        "qa", description="Active mode for the session"
    )

class ChatMessage(BaseModel):
    """Single chat message stored in a session"""
    session_id: str = Field(..., description="Associated session id")
    role: Literal["user", "assistant", "system"] = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    mode: Optional[Literal["qa", "writing", "translation", "summary", "student", "professional", "fun"]] = None
    meta: Optional[dict] = None

class ImageRequest(BaseModel):
    prompt: str = Field(..., description="Prompt to generate image from")
    style: Optional[str] = Field(None, description="Optional style hint")
