from typing import Optional

from pydantic import BaseModel, Field

from browser_use.controller.views import (
	ControllerAction,
)


class AgentOutput(ControllerAction):
	valuation: str = Field(description='Result of previous action')
	memory: str = Field(description='Current progress state')
	next_goal: str = Field(description='Next immediate goal')


class ClickElementControllerHistoryItem(BaseModel):
	xpath: str | None
	id: str | None
	num_clicks: int | None


class InputTextControllerHistoryItem(BaseModel):
	xpath: str | None
	id: str | None
	input_text: str | None


class AgentHistory(AgentOutput):
	click_element: Optional[ClickElementControllerHistoryItem] = None
	input_text: Optional[InputTextControllerHistoryItem] = None
	url: str
