from typing import Optional

from pydantic import BaseModel


class CodeDiff(BaseModel):
    diff: str
    file_path: str
    old_file_path: Optional[str] = None
    change_type: str
    current_file_content: Optional[str] = None  # Full current file content for excerpt extraction
