import logging
import time
from functools import wraps
from typing import Any, Callable, Coroutine, ParamSpec, TypeVar

# Configure root logger to ERROR to suppress third-party logs
# logging.getLogger().setLevel(logging.ERROR)
# logging.getLogger('WDM').setLevel(logging.ERROR)  # WebDriver Manager
# logging.getLogger('httpx').setLevel(logging.ERROR)  # HTTP requests
# logging.getLogger('selenium').setLevel(logging.ERROR)  # Selenium
# logging.getLogger('urllib3').setLevel(logging.ERROR)  # URLLib
# logging.getLogger('asyncio').setLevel(logging.ERROR)  # Asyncio

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


# Define generic type variables for return type and parameters
R = TypeVar('R')
P = ParamSpec('P')


def time_execution_sync(additional_text: str = '') -> Callable[[Callable[P, R]], Callable[P, R]]:
	def decorator(func: Callable[P, R]) -> Callable[P, R]:
		@wraps(func)
		def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
			start_time = time.time()
			result = func(*args, **kwargs)
			execution_time = time.time() - start_time
			logger.debug(f'{additional_text} Execution time: {execution_time:.2f} seconds')
			return result

		return wrapper

	return decorator


def time_execution_async(
	additional_text: str = '',
) -> Callable[[Callable[P, Coroutine[Any, Any, R]]], Callable[P, Coroutine[Any, Any, R]]]:
	def decorator(func: Callable[P, Coroutine[Any, Any, R]]) -> Callable[P, Coroutine[Any, Any, R]]:
		@wraps(func)
		async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
			start_time = time.time()
			result = await func(*args, **kwargs)
			execution_time = time.time() - start_time
			logger.debug(f'{additional_text} Execution time: {execution_time:.2f} seconds')
			return result

		return wrapper

	return decorator
