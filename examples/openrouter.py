import asyncio
import os
from typing import Any

# logging
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, SecretStr

from browser_use import Agent

load_dotenv()

api_key = os.getenv('OPENROUTER_API_KEY')
base_url = os.getenv('OPENROUTER_BASE_URL')
# model_name = 'minimax/minimax-01'
model_name = 'openai/gpt-4o'

llm = ChatOpenAI(
	api_key=api_key,
	base_url=base_url,
	model_name=model_name,
)


async def run_search():
	agent = Agent(
		task=(
			'Go to url r/LocalLLaMA subreddit and search for "browser use" in the search bar and click on the first post and find the funniest comment'
		),
		llm=llm,
		max_actions_per_step=4,
	)
	await agent.run()


if __name__ == '__main__':
	asyncio.run(run_search())
