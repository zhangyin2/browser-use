"""
Simple try of the agent.

@dev You need to add OPENAI_API_KEY to your environment variables.
"""

import os
import sys

from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

from langchain_openai import ChatOpenAI

from browser_use import Agent

llm = ChatOpenAI(model='gpt-4o')
browser = (
	Browser(
		config=BrowserConfig(
			disable_security=False,
			new_context_config=BrowserContextConfig(wait_between_actions=0),
		),
	),
)

agent = Agent(
	task='search for openai and open the first 10 links in new tabs.',  # after you have all open, visit all of them and return all email addresses you could find in done',
	# task='Go to amazon.com, search for laptop, sort by best rating, and give me the price of the first result',
	llm=llm,
	plan_task=True,
	max_actions_per_step=4,
)


async def main():
	await agent.run(max_steps=20)
	input('Press Enter to continue...')


asyncio.run(main())
