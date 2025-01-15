from typing import Literal, Optional

from pydantic import BaseModel, Field


class DoneAction(BaseModel):
	text: str = Field(..., description='The text to output to the user')
	status: Literal['success', 'failure', 'unknown'] = Field(
		..., description='If the task was successful completed, failed or you are unsure'
	)
	status_reason: str = Field(..., description='The reason for the status')
