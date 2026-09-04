from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import List, Dict, Any, Optional
from app.api.auth import verify_internal_secret
from app.api.schemas import TopicItem
from app.api.services.preview_service import fetch_news_preview
from app.api.services.user_pipeline import run_user_pipeline

router = APIRouter(
    prefix="/internal",
    tags=["Internal"],
    dependencies=[Depends(verify_internal_secret)]
)

from typing import List, Dict, Any, Optional, Union

class InternalPreviewRequest(BaseModel):
    topics: List[Union[TopicItem, str]] = Field(..., min_length=1)

class InternalPipelineRequest(BaseModel):
    email: EmailStr
    topics: Optional[List[Union[TopicItem, str]]] = None
    dry_run: bool = False

@router.post("/news-preview", status_code=status.HTTP_200_OK)
async def internal_news_preview(payload: InternalPreviewRequest) -> Dict[str, Any]:
    """Protected internal endpoint for fetching and summarizing live news preview."""
    try:
        parsed_topics = [TopicItem.parse_item(t) for t in payload.topics]
        preview_data = await fetch_news_preview(parsed_topics)
        return {"status": "success", **preview_data}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preview generation failed: {str(e)}"
        )

@router.post("/run-pipeline", status_code=status.HTTP_200_OK)
async def internal_run_pipeline(payload: InternalPipelineRequest) -> Dict[str, Any]:
    """Protected internal endpoint for running full scraping, curation, and email delivery."""
    try:
        parsed_topics = [TopicItem.parse_item(t).model_dump() for t in payload.topics] if payload.topics else None
        result = await run_user_pipeline(email=payload.email, topics=parsed_topics, dry_run=payload.dry_run)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline execution failed: {str(e)}"
        )
