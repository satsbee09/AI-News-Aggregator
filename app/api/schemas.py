from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Literal
from datetime import datetime

class TopicItem(BaseModel):
    name: str = Field(..., min_length=1, description="Topic name / query")
    scope: Literal["local", "national", "international", "general", "weather", "sports", "ai"] = "general"
    category: Optional[str] = "general"

class ScheduleSettings(BaseModel):
    time: str = Field(default="07:30", description="Delivery time in HH:MM (24-hour format)")
    frequency: Literal["daily", "every_6_hours", "every_12_hours"] = "daily"
    timezone: str = Field(default="Asia/Kolkata", description="IANA timezone name")

class UserCreateRequest(BaseModel):
    email: EmailStr

class UserTopicsUpdateRequest(BaseModel):
    topics: List[TopicItem] = Field(..., min_length=1, description="List of at least one selected topic")

class UserResponse(BaseModel):
    email: str
    topics: List[TopicItem] = []
    schedule: ScheduleSettings = Field(default_factory=ScheduleSettings)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
