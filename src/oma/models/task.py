from pydantic import BaseModel, Field


class TaskDefinition(BaseModel):
    id: str
    slug: str
    category: str
    title: str
    description: str
    prompt: str
    post_process: list[str] = Field(default_factory=list)
    models: list[str] | str = "all"