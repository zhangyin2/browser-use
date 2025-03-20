import asyncio
import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import SecretStr

from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
	raise ValueError('GEMINI_API_KEY is not set')
llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash-exp', api_key=SecretStr(api_key))
browser = Browser(
	config=BrowserConfig(
		new_context_config=BrowserContextConfig(save_downloads_path=os.path.join(os.path.expanduser('~'), 'downloads'))
	)
)


async def run_download():
	agent = Agent(
		task=('Go to https://v0-download-and-upload-text.vercel.app/" and download the file.'),
		llm=llm,
		max_actions_per_step=8,
		use_vision=True,
		browser=browser,
		save_conversation_path='~/Downloads',
	)

	await agent.run(max_steps=25)

	print(agent.browser_context.state.downloaded_files, '---', 'downloaded_files')

	await browser.close()


if __name__ == '__main__':
	asyncio.run(run_download())
