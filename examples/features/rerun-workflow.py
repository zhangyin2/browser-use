import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from browser_use import Agent

load_dotenv()

# Initialize the model
llm = ChatOpenAI(
	model='gpt-4o',
	temperature=0.0,
)

task = 'search for "founders of browser-use" on google click on the first link.'


agent = Agent(task=task, llm=llm)


async def main():
	await agent.run()
	# # save history
	agent.save_history('simple.json', exclude_screenshots=True)

	await agent.load_and_rerun('simple.json')


if __name__ == '__main__':
	asyncio.run(main())
