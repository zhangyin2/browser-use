import os
import re
import sys
from typing import List

import yaml

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from browser_use import Agent

load_dotenv()


def save_workflow_as_yaml(history: List[dict], output_file: str):
	"""Convert workflow history to simple YAML format with variable placeholders."""
	workflow = []

	for step in history:
		if 'search_google' in step:
			workflow.append(
				{
					'search_google': {
						'query': 'about {{company}}'  # Replace with variable placeholder
					}
				}
			)
		elif 'input_text' in step:
			workflow.append({'input_text': {'text': step['input_text']['text']}})
		elif 'llm_call' in step:
			workflow.append({'llm_call': {'task': step['llm_call']['task']}})

	# Save as YAML
	with open(output_file, 'w') as f:
		yaml.safe_dump(workflow, f, sort_keys=False, default_flow_style=False)


def load_workflow(yaml_file: str, **variables) -> List[dict]:
	"""Load workflow from YAML and replace variables."""
	# Load YAML file
	with open(yaml_file, 'r') as f:
		workflow = yaml.safe_load(f)

	# Convert to string for variable replacement
	workflow_str = yaml.safe_dump(workflow)

	# Replace all variables
	for var_name, value in variables.items():
		pattern = r'\{\{' + var_name + r'\}\}'
		workflow_str = re.sub(pattern, str(value), workflow_str)

	# Convert back to Python object
	return yaml.safe_load(workflow_str)


# Initialize the model
llm = ChatOpenAI(
	model='gpt-4o',
	temperature=0.0,
)

task = 'search for "founders of browser-use" on google click on the first link.'

agent = Agent(task=task, llm=llm)


async def main():
	# Run initial workflow
	await agent.run()

	# Save workflow as YAML template
	save_workflow_as_yaml(agent.history, 'workflow.yaml')

	# Example: Load workflow with variables
	workflow = load_workflow('workflow.yaml', company='Browser Use', founder='John Smith')

	# Run the workflow
	await agent.load_and_rerun(workflow)


if __name__ == '__main__':
	asyncio.run(main())
