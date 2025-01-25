from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from browser_use import Agent

load_dotenv()
llm = ChatOpenAI(model='gpt-4o')


async def main():
	agent1 = Agent(
		task='Go to google and search for browser-use, click on the first result',
		llm=llm,
	)
	history = await agent1.run(max_steps=10)

	agent1.save_history('AgentHistory.json')

	print('\n\nRerunning the agent\n\n')
	agent2 = Agent(
		task='',
		llm=llm,
	)
	history = await agent2.load_and_rerun('AgentHistory.json')


if __name__ == '__main__':
	import asyncio

	asyncio.run(main())
