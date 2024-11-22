"""
Simple try of the agent.

@dev You need to add ANTHROPIC_API_KEY to your environment variables.
"""

import os
import sys

from langchain_anthropic import ChatAnthropic
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from pydantic import SecretStr

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import asyncio

from browser_use import Agent
from browser_use.controller.service import Controller


def get_llm(provider: str):
	if provider == 'anthropic':
		return ChatAnthropic(
			model_name='claude-3-5-sonnet-20240620', timeout=25, stop=None, temperature=0.0
		)
	elif provider == 'openai':
		return ChatOpenAI(model='gpt-4o', temperature=0.0)
	elif provider == 'azure-openai':
		return AzureChatOpenAI(
			api_version='2024-10-21',
			model='gpt-4o',
			azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT', ''),
			api_key=SecretStr(os.getenv('AZURE_OPENAI_KEY', '')),
		)
	else:
		raise ValueError(f'Unsupported provider: {provider}')


parser = argparse.ArgumentParser()
parser.add_argument('query', type=str, help='The query to process')
parser.add_argument(
	'--provider',
	type=str,
	choices=['openai', 'anthropic', 'azure-openai'],
	default='openai',
	help='The model provider to use (default: openai)',
)

args = parser.parse_args()

llm = get_llm(args.provider)

agent = Agent(
	task=args.query,
	llm=llm,
	controller=Controller(keep_open=True),
	# save_conversation_path='./tmp/try_flight/',
)


async def main():
	await agent.run()


asyncio.run(main())
