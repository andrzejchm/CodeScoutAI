from pydantic import BaseModel


class ReviewCommandArgs(BaseModel):
    repo_path: str
    source: str
    target: str
    model: str
    openrouter_api_key: str | None
    openai_api_key: str | None
    claude_api_key: str | None
