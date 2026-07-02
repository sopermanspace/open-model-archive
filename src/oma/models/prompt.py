from pydantic import BaseModel, Field


class PromptFrontmatter(BaseModel):
    id: str
    version: str
    category: str
    title: str
    description: str = ""


class Prompt(BaseModel):
    meta: PromptFrontmatter
    body: str
    path: str
    sha256: str = ""

    @property
    def ref(self) -> str:
        return f"{self.meta.category}/{self.meta.id}@{self.meta.version}"

    @property
    def full_text(self) -> str:
        return self.body.strip()