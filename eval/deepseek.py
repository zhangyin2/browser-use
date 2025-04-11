import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from browser_use import Agent, Browser

load_dotenv()

api_key_deepseek = os.getenv('DEEPSEEK_API_KEY', '')
if not api_key_deepseek:
	raise ValueError('DEEPSEEK_API_KEY is not set')


async def run_agent(task: str, browser: Browser | None = None, max_steps: int = 38):
	browser = browser or Browser()
	llm = ChatOpenAI(
		base_url='https://api.deepseek.com/v1',
		model='deepseek-chat',
		api_key=SecretStr(api_key_deepseek),
	)
	agent = Agent(task=task, llm=llm, use_vision=False, browser=browser)
	result = await agent.run(max_steps=max_steps)
	return result
