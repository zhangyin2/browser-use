from asyncio import run

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from browser_use import Agent
from browser_use.utils import logger

logger.info('Starting agent')
logger.debug('Debug messages are enabled')
# model='qwen2.5:32b',
llm = ChatOllama(
	model='qwen2.5:32b-instruct',
	base_url='http://localhost:11434',
	temperature=0,
	format='json',
)
load_dotenv()
llm = ChatOpenAI(
	model='gpt-4o',
	temperature=0,
)
agent = Agent(
	task='Go to hackernews on show hn and give me top 10 post titles, their points and hours. Calculate for each the ratio of points per hour.',
	llm=llm,
	save_conversation_path='temp/new_format/',
)

run(agent.run())
