from pydantic import BaseModel

verdict = "Approve" | "Request Changes" | "Comment"

class line_change(BaseModel):
    line_number:int
    line_content:str
    action_required:str

class file_change(BaseModel):
    file_name:str
    line_changes:list[line_change]

class pr_agent_response(BaseModel):
    file_changes:list[file_change]
    verdict:verdict
    comment:str
    