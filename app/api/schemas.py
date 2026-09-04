from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import List, Optional, Literal, Union, Any
from datetime import datetime

class TopicItem(BaseModel):
    name: str = Field(..., min_length=1, description="Topic name / query")
    scope: str = Field(default="general", description="Topic scope/type")
    category: Optional[str] = Field(default="general", description="Category tag")

    @classmethod
    def parse_item(cls, val: Any) -> "TopicItem":
        if isinstance(val, str):
            return cls(name=val, scope="general", category="general")
        if isinstance(val, dict):
            return cls(**val)
        return val

class ScheduleSettings(BaseModel):
    time: str = Field(default="07:30", description="Delivery time in HH:MM (24-hour format)")
    frequency: Literal["daily", "every_6_hours", "every_12_hours"] = "daily"
    timezone: str = Field(default="Asia/Kolkata", description="IANA timezone name")
    enabled: bool = Field(default=True, description="Whether automated email digests are active")

class UserCreateRequest(BaseModel):
    email: EmailStr

class UserTopicsUpdateRequest(BaseModel):
    topics: List[TopicItem] = Field(..., min_length=1, description="List of at least one selected topic")

class UserResponse(BaseModel):
    email: str
    is_subscribed: bool = True
    topics: List[TopicItem] = []
    schedule: ScheduleSettings = Field(default_factory=ScheduleSettings)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
