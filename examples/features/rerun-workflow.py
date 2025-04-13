import os
import sys

from browser_use.workflow.views import Workflow

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from browser_use import Agent

load_dotenv()


# Example usage
async def main():
	# Initialize agent and LLM
	llm = ChatOpenAI(model='gpt-4o', temperature=0.0)

	# Create and run workflow
	workflow = Workflow('workflow.yaml', company_name='Browser Use', year='2024')
	agent = Agent(workflow=workflow, llm=llm, save_workflow_yaml=None)  # , save_workflow_yaml=None
	# agent = Agent(llm=llm, task="go to google and search for 'Browser Use'- click on the first search result and scroll down")
	history = await agent.run()


if __name__ == '__main__':
	asyncio.run(main())
