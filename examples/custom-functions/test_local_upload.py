import asyncio
from pathlib import Path

from langchain_openai import ChatOpenAI

from browser_use import Agent, Controller
from browser_use.browser.browser import Browser, BrowserConfig

# Create a test file
TEST_FILE_PATH = Path(__file__).parent / 'test_upload.txt'
with open(TEST_FILE_PATH, 'w') as f:
	f.write('This is a test file for upload functionality')

# Initialize browser and controller
browser = Browser(
	config=BrowserConfig(
		headless=False,  # Set to True if you don't need to see the browser
		chrome_instance_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
	)
)

# Simple controller without user settings for local file upload
controller = Controller()


async def main():
	task = f"""
    1. Go togo to https://kzmpmkh2zfk1ojnpxfn1.lite.vusercontent.net/ and upload to each upload field my file
    2. Upload the file at {TEST_FILE_PATH}
    3. to each upload field
    """

	model = ChatOpenAI(model='gpt-4o')
	agent = Agent(
		task=task,
		llm=model,
		controller=controller,
		browser=browser,
	)

	try:
		await agent.run()
	finally:
		# Clean up
		await browser.close()


if __name__ == '__main__':
	asyncio.run(main())
