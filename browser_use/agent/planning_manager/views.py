from pydantic import BaseModel, Field


class TaskPlan(BaseModel):
	"""Structured task plan with rich metadata"""

	task: str = Field(..., description="Reformulated step by step plan of the user's original task")
	short_summary: str = Field(..., description='A one sentence summary of the task')
	tags: list[str] = Field(
		...,
		description='Keywords associated with the task, e.g. "shopping", "research", "login", "data extraction", "QA testing", "social media"',
	)
	estimated_difficulty: int = Field(
		...,
		description='Estimate of complexity level (1-10)',
	)
	estimated_value: int = Field(
		...,
		description='Estimate of the value of the task (1-10)',
	)
