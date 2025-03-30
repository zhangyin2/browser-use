import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from browser_use import Agent, Browser, BrowserConfig

load_dotenv()

# Initialize the model
llm = ChatOpenAI(
	model='gpt-4o',
	temperature=0.0,
)
browser = Browser(
	config=BrowserConfig(
		# NOTE: you need to close your chrome browser - so that this can open your browser in debug mode
		browser_instance_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
	)
)

task = 'search for "founders of browser-use" on google click on the first link.'


agent = Agent(task=task, llm=llm, browser=browser)


async def main():
	await agent.run()
	# # save history
	agent.save_history('simple.json', exclude_screenshots=True)

	await agent.load_and_rerun('simple.json')


if __name__ == '__main__':
	asyncio.run(main())
