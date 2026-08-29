from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FileChangePayload(BaseModel):
    file_path: str | None = Field(None, description="Path of the file being changed")
    old_content: str | None = Field(None, description="Original content of the file")
    new_content: str | None = Field(None, description="Proposed new content of the file")
    created_by: str | None = Field(None, description="User ID of the creator")
    created_by_dept: str | None = Field(None, description="Department of the creator")
    change_summary: str | None = Field(None, description="Summary description of the change")

    model_config = ConfigDict(extra="allow")


class ProposalResponse(BaseModel):
    id: str | None = Field(None, description="Unique identifier of the proposal")
    created_at: str | None = Field(None, description="Timestamp when proposal was created")
    status: str | None = Field(None, description="Status of the proposal (e.g. pending, approved, rejected)")
    type: str | None = Field(None, description="Type of change proposal")
    request_payload: FileChangePayload | dict[str, Any] | None = Field(
        None, description="Payload details of the proposal"
    )
    approved_by: str | None = Field(None, description="User ID who approved or rejected")
    approved_at: str | None = Field(None, description="Timestamp when decision was made")
    executed_at: str | None = Field(None, description="Timestamp when proposal was executed")
    execution_log: str | None = Field(None, description="Log output from execution")

    model_config = ConfigDict(from_attributes=True)


class CreateProposalRequest(BaseModel):
    file_path: str = Field(..., description="Path of the target file to modify")
    new_content: str = Field(..., description="New content for the target file")
    summary: str = Field("AI Generated Fix", description="Summary description of the proposed change")


class ProposalActionResultResponse(BaseModel):
    status: str = Field(..., description="Resulting status of the action")
    message: str = Field(..., description="Human-readable result message")
    details: ProposalResponse | dict[str, Any] = Field(..., description="Details of the updated proposal")
