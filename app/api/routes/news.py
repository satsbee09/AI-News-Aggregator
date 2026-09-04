from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.api.schemas import TopicItem
from app.api.services.preview_service import fetch_news_preview

router = APIRouter(prefix="/api/news", tags=["News"])

class NewsPreviewRequest(BaseModel):
    topics: List[TopicItem] = Field(..., min_length=1, description="List of topics to preview")

@router.post("/preview", status_code=status.HTTP_200_OK)
async def preview_news_feed(payload: NewsPreviewRequest) -> Dict[str, Any]:
    """Instant live preview endpoint: fetches and summarizes news for selected topics on-demand."""
    if not payload.topics:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one topic must be provided for preview."
        )
    
    preview_data = await fetch_news_preview(payload.topics)
    return preview_data
