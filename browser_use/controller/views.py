from typing import Optional, Union
from urllib.parse import urlparse

from pydantic import BaseModel, model_validator, validator


# Action Input Models
class SearchGoogleAction(BaseModel):
	query: str


class GoToUrlAction(BaseModel):
	url: str


class ClickElementAction(BaseModel):
	index: int
	xpath: Optional[str] = None


class InputTextAction(BaseModel):
	index: int
	text: str
	xpath: Optional[str] = None


class DoneAction(BaseModel):
	text: str


class SwitchTabAction(BaseModel):
	page_id: int


class OpenTabAction(BaseModel):
	url: str


class ScrollAction(BaseModel):
	amount: Optional[int] = None  # The number of pixels to scroll. If None, scroll down/up one page


class FileUploadAction(BaseModel):
	index: int
	file_path: str  # Can be local path or S3 URL
	wait_for_navigation: bool = False
	timeout: Optional[int] = 30000  # 30 seconds default timeout

	@validator('file_path')
	def validate_file_path(cls, v):
		# Check if it's an S3 URL
		parsed = urlparse(v)
		if parsed.scheme == 's3':
			return v
		elif parsed.scheme in ('http', 'https') and 's3' in parsed.netloc:
			return v
		elif parsed.scheme in ('', 'file'):
			# Local file path
			return v.replace('file://', '')
		else:
			# Assume local path if no scheme
			return v


class SendKeysAction(BaseModel):
	keys: str


class NoParamsAction(BaseModel):
	"""
	Accepts absolutely anything in the incoming data
	and discards it, so the final parsed model is empty.
	"""

	@model_validator(mode='before')
	def ignore_all_inputs(cls, values):
		# No matter what the user sends, discard it and return empty.
		return {}

	class Config:
		# If you want to silently allow unknown fields at top-level,
		# set extra = 'allow' as well:
		extra = 'allow'
