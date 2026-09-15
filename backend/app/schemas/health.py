from pydantic import BaseModel, Field


class RootResponse(BaseModel):
    message: str = Field(..., description="API welcome message")
    version: str = Field(..., description="Application version")
    status: str = Field(..., description="Application status")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Health check status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Application version")
