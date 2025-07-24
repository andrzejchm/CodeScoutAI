from typing import Optional

from pydantic import BaseModel


class CodeDiff(BaseModel):
    diff: str
    file_path: str
    old_file_path: Optional[str] = None
    change_type: str
