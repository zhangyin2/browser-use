import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import os

from langchain_openai import AzureChatOpenAI
from pydantic import SecretStr

from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig, BrowserContextConfig

browser = Browser(
	config=BrowserConfig(
		headless=False,  # This is True in production
		disable_security=True,
		new_context_config=BrowserContextConfig(
			disable_security=True,
			wait_for_network_idle_page_load_time=1,
			# minimum_wait_page_load_time=3,  # 3 on prod
			maximum_wait_page_load_time=5,  # 20 on prod
			# no_viewport=True,
			browser_window_size={
				'width': 1280,
				'height': 1100,
			},
			# trace_path='./tmp/web_voyager_agent',
		),
	)
)
llm = AzureChatOpenAI(
	model='gpt-4o',
	api_version='2024-10-21',
	azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT', ''),
	api_key=SecretStr(os.getenv('AZURE_OPENAI_KEY', '')),
)


# class CustomSystemPrompt(SystemPrompt):
# 	def important_rules(self) -> str:
# 		existing_rules = super().important_rules()
# 		new_rules = """
# 9. EXTRA RULES:
# - assume that children are 10 years old
# - make sure to scroll down to find all filters the task requires
# """
# 		return f'{existing_rules}\n{new_rules}'


TASK = """
Find the lowest-priced one-way flight from Cairo to Montreal on February 21, 2025, including the total travel time and number of stops. on https://www.google.com/travel/flights/
"""
# TASK = """
# Browse Coursera, which universities offer Master of Advanced Study in Engineering degrees? Tell me what is the latest application deadline for this degree? on https://www.coursera.org/"""
# TASK = """
# Find the most recent sports analysis article on BBC News related to the English Premier League and summarize its key insights. on https://www.bbc.com/news/
# """
# TASK = """
# Find the most recent sports analysis article on BBC News related to the English Premier League and summarize its key insights. on https://www.bbc.com/news/
# """


async def main():
	agent = Agent(
		task=TASK,
		llm=llm,
		# system_prompt_class=CustomSystemPrompt,
		browser=browser,
		validate_output=True,
	)
	history = await agent.run(max_steps=30)
	history.save_to_file('./tmp/history.json')


if __name__ == '__main__':
	asyncio.run(main())
