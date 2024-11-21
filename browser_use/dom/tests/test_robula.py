import time

from bs4 import BeautifulSoup

from browser_use.browser.service import Browser
from browser_use.dom._robula_plus.service import RobulaPlus
from browser_use.dom.service import DomService


async def test_robula_xpath_generation():
	browser = Browser(headless=False)
	page = await browser.get_current_page()
	dom_service = DomService(page)
	robula_service = RobulaPlus()

	await page.goto('https://kayak.com')

	# Wait for page to load
	time.sleep(3)

	content = await page.content()
	soup = BeautifulSoup(content, 'html.parser')

	# Let's get a specific element (e.g., the search button) and generate its Robula+ xpath
	current_xpath = '/html/body/div[4]/div/div[2]/div/div/div[3]/div/div[1]/button[1]/div'
	element = soup.select_one(
		'button.RxNS.RxNS-mod-stretch.RxNS-mod-variant-outline[role="button"]'
	)

	if element is None:
		raise ValueError('Element not found')

	robula_xpath = robula_service.get_robust_xpath(soup, element, current_xpath)

	print(f'Generated Robula+ XPath: {robula_xpath}')

	# Verify the xpath works by finding the element again
	found_element = await page.query_selector(f'xpath={robula_xpath}')
	assert found_element is not None, 'Generated XPath could not find the element'

	input('Press Enter to continue...')
