from pydantic import BaseModel


class AgentInfo(BaseModel):
    name: str
    description: str
    status: str = "available"


class AgentListResponse(BaseModel):
    agents: list[AgentInfo]
