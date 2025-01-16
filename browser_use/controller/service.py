import asyncio
import json
import logging

from main_content_extractor import MainContentExtractor
from playwright.async_api import Page

from browser_use.agent.views import ActionModel, ActionResult
from browser_use.browser.context import BrowserContext
from browser_use.controller.registry.service import Registry
from browser_use.controller.views import DoneAction
from browser_use.utils import time_execution_async, time_execution_sync

logger = logging.getLogger(__name__)


class Controller:
	def __init__(
		self,
		exclude_actions: list[str] = [],
	):
		self.exclude_actions = exclude_actions
		self.registry = Registry(self.exclude_actions)
		self._register_default_actions()

	def _register_default_actions(self):
		"""Register all default browser actions"""

		# Basic Navigation Actions
		@self.registry.action(
			'This does a google search with the given query inside the current tab',
			requires_browser=True,
		)
		async def search_google(query: str, browser: BrowserContext):
			page = await browser.get_current_page()
			await page.goto(f'https://www.google.com/search?q={query}&udm=14')
			await page.wait_for_load_state()
			msg = f'🔍  Searched for "{query}" in Google'
			logger.info(msg)
			return ActionResult(extracted_content=msg, include_in_memory=True)

		@self.registry.action('This navigates directlyto the url', requires_browser=True)
		async def go_to_url(url: str, browser: BrowserContext):
			page = await browser.get_current_page()
			await page.goto(url)
			await page.wait_for_load_state()
			msg = f'🔗  Navigated to {url}'
			logger.info(msg)
			return ActionResult(extracted_content=msg, include_in_memory=True)

		@self.registry.action(
			'This navigates to the previous page num_times times (normally 1)',
			requires_browser=True,
		)
		async def go_back(num_times: int, browser: BrowserContext):
			page = await browser.get_current_page()
			for _ in range(num_times):
				await page.go_back()
				await page.wait_for_load_state()
			msg = f'🔙  Navigated back {num_times} times'
			logger.info(msg)
			return ActionResult(extracted_content=msg, include_in_memory=True)

		# Element Interaction Actions
		@self.registry.action(
			'Click on the interactive element with the index', requires_browser=True
		)
		async def click_element(index: int, browser: BrowserContext):
			session = await browser.get_session()
			state = session.cached_state

			if index not in state.selector_map:
				raise Exception(
					f'Element with index {index} does not exist - retry or use alternative actions'
				)

			element_node = state.selector_map[index]
			initial_pages = len(session.context.pages)

			# if element has file uploader then dont click
			if await browser.is_file_uploader(element_node):
				msg = f'Index {index} - has an element which opens file upload dialog. To upload files please use a specific function to upload files '
				logger.info(msg)
				return ActionResult(extracted_content=msg, include_in_memory=True)

			msg = None

			try:
				await browser._click_element_node(element_node)
				msg = f'🖱️  Clicked button with index {index}: {element_node.get_all_text_till_next_clickable_element(max_depth=2)}'

				logger.info(msg)
				logger.debug(f'Element xpath: {element_node.xpath}')
				if len(session.context.pages) > initial_pages:
					new_tab_msg = 'New tab opened - switching to it'
					msg += f' - {new_tab_msg}'
					logger.info(new_tab_msg)
					await browser.switch_to_tab(-1)
				return ActionResult(extracted_content=msg, include_in_memory=True)
			except Exception as e:
				logger.warning(
					f'Element no longer available with index {index} - most likely the page changed'
				)
				return ActionResult(error=str(e))

		@self.registry.action(
			'Input text into a input interactive element',
			requires_browser=True,
		)
		async def input_text(index: int, text: str, browser: BrowserContext):
			session = await browser.get_session()
			state = session.cached_state

			if index not in state.selector_map:
				raise Exception(
					f'Element index {index} does not exist - retry or use alternative actions'
				)

			element_node = state.selector_map[index]
			await browser._input_text_element_node(element_node, text)
			msg = f'⌨️  Input "{text}" into index {index}'
			logger.info(msg)
			logger.debug(f'Element xpath: {element_node.xpath}')
			return ActionResult(extracted_content=msg, include_in_memory=True)

		# Tab Management Actions
		@self.registry.action(
			'This switches the tab to the page with the index', requires_browser=True
		)
		async def switch_tab(page_id: int, browser: BrowserContext):
			await browser.switch_to_tab(page_id)
			# Wait for tab to be ready
			page = await browser.get_current_page()
			await page.wait_for_load_state()
			msg = f'🔄  Switched to tab {page_id}'
			logger.info(msg)
			return ActionResult(extracted_content=msg, include_in_memory=True)

		@self.registry.action('This opens the url in a new tab', requires_browser=True)
		async def open_tab(url: str, browser: BrowserContext):
			await browser.create_new_tab(url)
			msg = f'🔗  Opened new tab with {url}'
			logger.info(msg)
			return ActionResult(extracted_content=msg, include_in_memory=True)

		# Content Actions
		@self.registry.action(
			'Extract page content to get the text or markdown with links if include_links is set to true',
			requires_browser=True,
		)
		async def extract_content(include_links: bool, browser: BrowserContext):
			page = await browser.get_current_page()
			output_format = 'markdown' if include_links else 'text'
			html = await page.content()
			content = MainContentExtractor.extract(  # type: ignore
				html=html,
				output_format=output_format,
			)
			msg = f'📄  Extracted page as {output_format}\n: {content}\n'
			logger.info(msg)
			return ActionResult(extracted_content=msg)

		@self.registry.action('Complete task', param_model=DoneAction)
		async def done(params: DoneAction):
			return ActionResult(
				is_done=True,
				extracted_content=params.text,
				status=params.status,
				status_reason=params.status_reason,
			)

		@self.registry.action(
			'Scroll down the page by pixel amount',
			requires_browser=True,
		)
		async def scroll_down(amount: int, browser: BrowserContext):
			page = await browser.get_current_page()
			await page.evaluate(f'window.scrollBy(0, {amount});')

			msg = f'🔍  Scrolled down the page by {amount} pixels'
			logger.info(msg)
			return ActionResult(
				extracted_content=msg,
				include_in_memory=True,
			)

		# scroll up
		@self.registry.action(
			'Scroll up the page by pixel amount',
			requires_browser=True,
		)
		async def scroll_up(amount: int, browser: BrowserContext):
			page = await browser.get_current_page()
			await page.evaluate(f'window.scrollBy(0, -{amount});')

			msg = f'🔍  Scrolled up the page by {amount} pixels'
			logger.info(msg)
			return ActionResult(
				extracted_content=msg,
				include_in_memory=True,
			)

		# send keys
		@self.registry.action(
			'Send strings of special keys like Backspace, Insert, PageDown, Delete, Enter, Shortcuts such as `Control+o`, `Control+Shift+T` are supported as well. This is used in keyboard.press(keys). Be aware of different operating systems and their shortcuts',
			requires_browser=True,
		)
		async def send_keys(keys: str, browser: BrowserContext):
			page = await browser.get_current_page()
			await page.keyboard.press(keys)
			msg = f'⌨️  Sent keys: {keys}'
			logger.info(msg)
			return ActionResult(extracted_content=msg, include_in_memory=True)

		@self.registry.action(
			description='This will scroll to the first occurence of the text',
			requires_browser=True,
		)
		async def scroll_to_text(text: str, browser: BrowserContext):  # type: ignore
			page = await browser.get_current_page()
			try:
				# Try different locator strategies
				locators = [
					page.get_by_text(text, exact=False),
					page.locator(f'text={text}'),
					page.locator(f"//*[contains(text(), '{text}')]"),
				]

				for locator in locators:
					try:
						# First check if element exists and is visible
						if await locator.count() > 0 and await locator.first.is_visible():
							await locator.first.scroll_into_view_if_needed()
							await asyncio.sleep(0.5)  # Wait for scroll to complete
							msg = f'🔍  Scrolled to text: {text}'
							logger.info(msg)
							return ActionResult(extracted_content=msg, include_in_memory=True)
					except Exception as e:
						logger.debug(f'Locator attempt failed: {str(e)}')
						continue

				msg = f"Text '{text}' not found or not visible on page"
				logger.info(msg)
				return ActionResult(extracted_content=msg, include_in_memory=True)

			except Exception as e:
				msg = f"Failed to scroll to text '{text}': {str(e)}"
				logger.error(msg)
				return ActionResult(error=msg, include_in_memory=True)

		@self.registry.action(
			description='Get all options from a native dropdown',
			requires_browser=True,
		)
		async def get_dropdown_options(index: int, browser: BrowserContext) -> ActionResult:
			"""Get all options from a native dropdown"""
			page = await browser.get_current_page()
			selector_map = await browser.get_selector_map()
			dom_element = selector_map[index]

			try:
				# Frame-aware approach since we know it works
				all_options = []
				frame_index = 0

				for frame in page.frames:
					try:
						options = await frame.evaluate(
							"""
							(xpath) => {
								const select = document.evaluate(xpath, document, null,
									XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
								if (!select) return null;
								
								return {
									options: Array.from(select.options).map(opt => ({
										text: opt.text, //do not trim, because we are doing exact match in select_dropdown_option
										value: opt.value,
										index: opt.index
									})),
									id: select.id,
									name: select.name
								};
							}
						""",
							dom_element.xpath,
						)

						if options:
							logger.debug(f'Found dropdown in frame {frame_index}')
							logger.debug(f'Dropdown ID: {options["id"]}, Name: {options["name"]}')

							formatted_options = []
							for opt in options['options']:
								# encoding ensures AI uses the exact string in select_dropdown_option
								encoded_text = json.dumps(opt['text'])
								formatted_options.append(f'{opt["index"]}: text={encoded_text}')

							all_options.extend(formatted_options)

					except Exception as frame_e:
						logger.debug(f'Frame {frame_index} evaluation failed: {str(frame_e)}')

					frame_index += 1

				if all_options:
					msg = '\n'.join(all_options)
					msg += '\nUse the exact text string in select_dropdown_option'
					logger.info(msg)
					return ActionResult(extracted_content=msg, include_in_memory=True)
				else:
					msg = 'No options found in any frame for dropdown'
					logger.info(msg)
					return ActionResult(extracted_content=msg, include_in_memory=True)

			except Exception as e:
				logger.error(f'Failed to get dropdown options: {str(e)}')
				msg = f'Error getting options: {str(e)}'
				logger.info(msg)
				return ActionResult(extracted_content=msg, include_in_memory=True)

		@self.registry.action(
			description='Select dropdown option for interactive element index by the text of the option you want to select',
			requires_browser=True,
		)
		async def select_dropdown_option(
			index: int,
			text: str,
			browser: BrowserContext,
		) -> ActionResult:
			"""Select dropdown option by the text of the option you want to select"""
			page = await browser.get_current_page()
			selector_map = await browser.get_selector_map()
			dom_element = selector_map[index]

			# Validate that we're working with a select element
			if dom_element.tag_name != 'select':
				logger.error(
					f'Element is not a select! Tag: {dom_element.tag_name}, Attributes: {dom_element.attributes}'
				)
				msg = f'Cannot select option: Element with index {index} is a {dom_element.tag_name}, not a select'
				return ActionResult(extracted_content=msg, include_in_memory=True)

			logger.debug(f"Attempting to select '{text}' using xpath: {dom_element.xpath}")
			logger.debug(f'Element attributes: {dom_element.attributes}')
			logger.debug(f'Element tag: {dom_element.tag_name}')

			try:
				frame_index = 0
				for frame in page.frames:
					try:
						logger.debug(f'Trying frame {frame_index} URL: {frame.url}')

						# First verify we can find the dropdown in this frame
						find_dropdown_js = """
							(xpath) => {
								try {
									const select = document.evaluate(xpath, document, null,
										XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
									if (!select) return null;
									if (select.tagName.toLowerCase() !== 'select') {
										return {
											error: `Found element but it's a ${select.tagName}, not a SELECT`,
											found: false
										};
									}
									return {
										id: select.id,
										name: select.name,
										found: true,
										tagName: select.tagName,
										optionCount: select.options.length,
										currentValue: select.value,
										availableOptions: Array.from(select.options).map(o => o.text.trim())
									};
								} catch (e) {
									return {error: e.toString(), found: false};
								}
							}
						"""

						dropdown_info = await frame.evaluate(find_dropdown_js, dom_element.xpath)

						if dropdown_info:
							if not dropdown_info.get('found'):
								logger.error(
									f'Frame {frame_index} error: {dropdown_info.get("error")}'
								)
								continue

							logger.debug(f'Found dropdown in frame {frame_index}: {dropdown_info}')

							# Rest of the selection code remains the same...
							select_option_js = """
								(params) => {
									try {
										const select = document.evaluate(params.xpath, document, null,
											XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
										if (!select || select.tagName.toLowerCase() !== 'select') {
											return {success: false, error: 'Select not found or invalid element type'};
										}
										
										const option = Array.from(select.options)
											.find(opt => opt.text === params.text);
										
										if (!option) {
											return {
												success: false, 
												error: 'Option not found',
												availableOptions: Array.from(select.options).map(o => o.text)
											};
										}
										
										select.value = option.value;
										select.dispatchEvent(new Event('change'));
										return {
											success: true, 
											selectedValue: option.value,
											selectedText: option.text
										};
									} catch (e) {
										return {success: false, error: e.toString()};
									}
								}
							"""

							params = {'xpath': dom_element.xpath, 'text': text}

							result = await frame.evaluate(select_option_js, params)
							logger.debug(f'Selection result: {result}')

							if result.get('success'):
								msg = f'Selected option {json.dumps(text)} (value={result.get("selectedValue")}'
								logger.info(msg + f' in frame {frame_index}')
								return ActionResult(extracted_content=msg, include_in_memory=True)
							else:
								logger.error(f'Selection failed: {result.get("error")}')
								if 'availableOptions' in result:
									logger.error(f'Available options: {result["availableOptions"]}')

					except Exception as frame_e:
						logger.error(f'Frame {frame_index} attempt failed: {str(frame_e)}')
						logger.error(f'Frame type: {type(frame)}')
						logger.error(f'Frame URL: {frame.url}')

					frame_index += 1

				msg = f"Could not select option '{text}' in any frame"
				logger.info(msg)
				return ActionResult(extracted_content=msg, include_in_memory=True)

			except Exception as e:
				msg = f'Selection failed: {str(e)}'
				logger.error(msg)
				return ActionResult(error=msg, include_in_memory=True)

	def action(self, description: str, **kwargs):
		"""Decorator for registering custom actions

		@param description: Describe the LLM what the function does (better description == better function calling)
		"""
		return self.registry.action(description, **kwargs)

	@time_execution_async('--multi-act')
	async def multi_act(
		self, actions: list[ActionModel], browser_context: BrowserContext
	) -> list[ActionResult]:
		"""Execute multiple actions"""
		results = []

		session = await browser_context.get_session()
		cached_selector_map = session.cached_state.selector_map
		cached_path_hashes = set(e.hash.branch_path_hash for e in cached_selector_map.values())
		await browser_context.remove_highlights()

		for i, action in enumerate(actions):
			if action.get_index() is not None and i != 0:
				new_state = await browser_context.get_state()
				new_path_hashes = set(
					e.hash.branch_path_hash for e in new_state.selector_map.values()
				)
				if not new_path_hashes.issubset(cached_path_hashes):
					# next action requires index but there are new elements on the page
					logger.info(f'Something new appeared after action {i} / {len(actions)}')
					break

			results.append(await self.act(action, browser_context))

			logger.debug(f'Executed action {i + 1} / {len(actions)}')
			if results[-1].is_done or results[-1].error or i == len(actions) - 1:
				break

			await asyncio.sleep(browser_context.config.wait_between_actions)
			# hash all elements. if it is a subset of cached_state its fine - else break (new elements on page)

		return results

	@time_execution_sync('--act')
	async def act(self, action: ActionModel, browser_context: BrowserContext) -> ActionResult:
		"""Execute an action"""
		try:
			for action_name, params in action.model_dump(exclude_unset=True).items():
				if params is not None:
					# remove highlights
					result = await self.registry.execute_action(
						action_name, params, browser=browser_context
					)
					if isinstance(result, str):
						return ActionResult(extracted_content=result)
					elif isinstance(result, ActionResult):
						return result
					elif result is None:
						return ActionResult()
					else:
						raise ValueError(f'Invalid action result type: {type(result)} of {result}')
			return ActionResult()
		except Exception as e:
			raise e
