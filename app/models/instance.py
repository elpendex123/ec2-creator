from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class InstanceCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Instance name")
    ami: str = Field(..., min_length=1, description="AMI ID")
    instance_type: str = Field(..., min_length=1, description="Instance type")
    storage_gb: int = Field(..., ge=1, description="Storage size in GB")


class InstanceResponse(BaseModel):
    id: str
    name: str
    public_ip: Optional[str] = ""
    ssh_string: Optional[str] = ""
    state: str
    ami: str
    instance_type: str
    backend_used: str
    created_at: datetime

    class Config:
        from_attributes = True


class InstanceListResponse(BaseModel):
    instances: List[InstanceResponse]
