from typing import Optional

from pydantic import BaseModel


class ReviewCommandArgs(BaseModel):
    repo_path: str
    source: str
    target: str
    staged: bool = False
    model: str
    openrouter_api_key: Optional[str]
    openai_api_key: Optional[str]
    claude_api_key: Optional[str]
