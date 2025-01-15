import asyncio
import time

from tokencost import count_string_tokens

from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.dom.service import DomService
from browser_use.utils import time_execution_sync


async def test_process_html_file():
	browser = Browser(config=BrowserConfig(headless=False))

	websites = [
		'https://kayak.com/flights',
		'https://immobilienscout24.de',
		'https://google.com',
		'https://amazon.com',
		'https://github.com',
	]

	async with await browser.new_context() as context:
		page = await context.get_current_page()
		dom_service = DomService(page)

		for website in websites:
			print(f'\n{"=" * 50}\nTesting {website}\n{"=" * 50}')
			await page.goto(website)
			time.sleep(2)  # Additional wait for dynamic content

			async def test_viewport(expansion: int, description: str):
				print(f'\n{description}:')
				dom_state = await time_execution_sync(f'get_clickable_elements ({description})')(
					dom_service.get_clickable_elements
				)(highlight_elements=True, viewport_expansion=expansion)

				elements = dom_state.element_tree
				selector_map = dom_state.selector_map
				element_count = len(selector_map.keys())
				token_count = count_string_tokens(
					elements.clickable_elements_to_string(), model='gpt-4o'
				)

				print(f'Number of elements: {element_count}')
				print(f'Token count: {token_count}')
				return element_count, token_count

			# Test initial viewport (0px expansion)
			viewport_count, viewport_tokens = await test_viewport(
				0, '1. Initial viewport (0px expansion)'
			)

			# Test with small expansion
			small_count, small_tokens = await test_viewport(100, '2. Small expansion (100px)')

			# Test with medium expansion
			medium_count, medium_tokens = await test_viewport(200, '3. Medium expansion (200px)')

			# Test all elements
			all_count, all_tokens = await test_viewport(-1, '4. All elements (-1 expansion)')

			# Print comparison summary
			print('\nComparison Summary:')
			print(f'Initial viewport (0px):   {viewport_count} elements, {viewport_tokens} tokens')
			print(
				f'Small expansion (100px):  {small_count} elements (+{small_count - viewport_count}), {small_tokens} tokens'
			)
			print(
				f'Medium expansion (200px): {medium_count} elements (+{medium_count - viewport_count}), {medium_tokens} tokens'
			)
			print(
				f'All elements (-1):        {all_count} elements (+{all_count - viewport_count}), {all_tokens} tokens'
			)

			input('\nPress Enter to continue to next website...')

			# Clear highlights before next website
			await page.evaluate(
				'document.getElementById("playwright-highlight-container")?.remove()'
			)


if __name__ == '__main__':
	asyncio.run(test_process_html_file())
