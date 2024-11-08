from pydantic import BaseModel

from browser_use.dom.views import ProcessedDomContent


# Exceptions
class BrowserException(Exception):
	pass


class TabInfo(BaseModel):
	handle: str
	url: str
	title: str
	is_current: bool


# Pydantic
class BrowserState(ProcessedDomContent):
	url: str
	title: str
	tab_infos: dict[str, TabInfo]
