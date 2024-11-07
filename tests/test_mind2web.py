"""
Test browser automation using Mind2Web dataset tasks with pytest framework.
"""

import json
import logging
import os
from typing import Any, Dict, List

import pytest
from langchain_openai import ChatOpenAI

from browser_use.agent.service import AgentService
from browser_use.controller.service import ControllerService
from browser_use.validator.service import ValidationService

logging.basicConfig(level=logging.INFO)

# Constants
MAX_STEPS = 50
TEST_SUBSET_SIZE = 2  # Number of test cases to run from dataset


@pytest.fixture(scope='session')
def test_cases() -> List[Dict[str, Any]]:
	"""Load test cases from Mind2Web dataset"""
	file_path = os.path.join(os.path.dirname(__file__), 'mind2web_data/processed.json')
	with open(file_path, 'r') as f:
		data = json.load(f)
	# Take a subset of test cases for faster testing
	return data[:TEST_SUBSET_SIZE]


@pytest.fixture(scope='session')
def llm():
	"""Initialize the language model"""
	return ChatOpenAI(model='gpt-4o')


@pytest.fixture(scope='function')
async def controller():
	"""Initialize and cleanup the controller for each test"""
	controller = ControllerService()
	yield controller
	await controller.close()


@pytest.fixture(scope='session')
def validator(llm):
	"""Initialize the validation service"""
	return ValidationService(llm)


@pytest.mark.parametrize(
	'website_group',
	[
		'booking',
		'expedia',
		'kayak',
		'united',
		'delta',
	],
)
class TestWebsiteGroup:
	"""Group tests by website for better organization"""

	@pytest.mark.asyncio
	async def test_website_tasks(
		self, website_group: str, test_cases: List[Dict[str, Any]], llm, controller, validator
	):
		"""Test all tasks for a specific website"""

		# Filter test cases for this website
		website_cases = [case for case in test_cases if case['website'] == website_group]

		if not website_cases:
			pytest.skip(f'No test cases for website: {website_group}')

		for case in website_cases:
			task = case['confirmed_task']

			# Initialize agent
			agent = AgentService(task, llm, controller, use_vision=True)

			# Run agent steps
			final_result = None
			for _ in range(MAX_STEPS):
				action, result = await agent.step()

				if result.done:
					final_result = result
					break

			# Validate results
			assert final_result is not None, f'Task timed out: {task}'

			current_state = controller.get_state()
			is_valid, reason = await validator.validate(
				task, current_state, final_result.extracted_content, case.get('action_reprs')
			)

			assert is_valid, f'Task validation failed: {task}\nReason: {reason}'


@pytest.mark.asyncio
async def test_random_samples(test_cases: List[Dict[str, Any]], llm, controller, validator):
	"""Test a random sampling of tasks across different websites"""
	import random

	# Take 5 random samples
	samples = random.sample(test_cases, 1)

	for case in samples:
		task = case['confirmed_task']
		agent = AgentService(task, llm, controller, use_vision=True)

		final_result = None
		for _ in range(MAX_STEPS):
			action, result = await agent.step()
			if result.done:
				final_result = result
				break

		assert final_result is not None, f'Random sample task timed out: {task}'

		current_state = controller.get_state()
		is_valid, reason = await validator.validate(
			task, current_state, final_result.extracted_content, case.get('action_reprs')
		)

		assert is_valid, f'Random sample task validation failed: {task}\nReason: {reason}'


def test_dataset_integrity(test_cases):
	"""Test the integrity of the test dataset"""
	required_fields = ['website', 'confirmed_task', 'action_reprs']
	missing_fields = []
	for case in test_cases:
		for field in required_fields:
			if field not in case:
				missing_fields.append(field)
		assert isinstance(case.get('confirmed_task'), str), 'Task must be string'
		assert isinstance(case.get('action_reprs'), list), 'Actions must be list'
		assert len(case.get('action_reprs', [])) > 0, 'Must have at least one action'

	assert not missing_fields, f'Missing fields: {missing_fields}'
