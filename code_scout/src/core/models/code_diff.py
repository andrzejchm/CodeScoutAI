from pydantic import BaseModel


class CodeDiff(BaseModel):
    diff: str
    file_path: str
    change_type: str
