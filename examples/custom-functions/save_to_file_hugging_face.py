import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from typing import List

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, SecretStr

from browser_use.agent.service import Agent
from browser_use.controller.service import Controller

# Initialize controller first
controller = Controller()


class Model(BaseModel):
	title: str
	url: str
	likes: int
	license: str


class Models(BaseModel):
	models: List[Model]


@controller.action('Save models', param_model=Models)
def save_models(params: Models):
	with open('models.txt', 'a') as f:
		for model in params.models:
			f.write(f'{model.title} ({model.url}): {model.likes} likes, {model.license}\n')

api_key_openrouter = os.getenv('OPENROUTER_API_KEY', '')
# video: https://preview.screen.studio/share/EtOhIk0P
async def main():
	task = 'Look up models with a license of mit and sort by most likes on Hugging face, save top 5 to file.'

	model = ChatOpenAI(
        base_url='https://api.seeknow.org/openrouter/api/v1',
        # model='openai/gpt-4.1',
        # model="openai/gpt-4.1-mini",
        model='openai/o4-mini',
        api_key=SecretStr(api_key_openrouter),
        temperature=0.1
    )
	agent = Agent(task=task, llm=model, controller=controller, enable_memory=False)

	await agent.run()


if __name__ == '__main__':
	asyncio.run(main())
