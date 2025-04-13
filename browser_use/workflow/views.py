import re
from typing import Any, Dict, List

import yaml
from pydantic import BaseModel

from browser_use.agent.views import AgentBrain, AgentOutput
from browser_use.controller.registry.views import ActionModel


class WorkflowAction(BaseModel):
	"""Base action in a workflow with parameters"""

	action_name: str
	parameters: Dict[str, Any]


class Workflow:
	"""Type-safe workflow container"""

	def __init__(self, yaml_file: str, **variables):
		self.yaml_file = yaml_file
		self.variables = variables
		self.raw_actions: List[WorkflowAction] = []
		self._load_workflow()
		self.step_index = 0
		self.actions: List[ActionModel] | None = None

	def get_raw_action_dict(self):
		"""Get the actions as a dictionary"""
		return [{action.action_name: action.parameters} for action in self.raw_actions]

	def get_current_action(self):
		"""Get the next step in the workflow"""
		if self.actions is None:
			raise ValueError('Actions not yet converted to ActionModel')

		if self.step_index >= self.length():
			return None
		step = self.actions[self.step_index]
		return step

	def get_current_model_output(self) -> None | AgentOutput:
		"""Get the next step in the workflow"""
		action = self.get_current_action()
		if not action:
			return None

		current_state = AgentBrain(
			evaluation_previous_goal='',
			memory='',
			next_goal='',
		)

		model_output = AgentOutput(
			current_state=current_state,
			action=[action],
		)
		return model_output

	def next_action(self):
		"""Move to the next step in the workflow"""
		self.step_index += 1

	def length(self):
		"""Get the length of the workflow"""
		return len(self.raw_actions)

	def _load_workflow(self):
		"""Load and parse workflow YAML"""
		# Load YAML file
		with open(self.yaml_file, 'r') as f:
			workflow_data = yaml.safe_load(f)

		# Convert to string for variable replacement
		workflow_str = yaml.safe_dump(workflow_data)

		# Replace variables
		for var_name, value in self.variables.items():
			pattern = r'\{\{' + var_name + r'\}\}'
			workflow_str = re.sub(pattern, str(value), workflow_str)

		# Parse back to Python object
		workflow_data = yaml.safe_load(workflow_str)

		# Convert each step to WorkflowAction
		for step_data in workflow_data:
			# Each step should have exactly one key (action name) and its parameters
			action_name = next(iter(step_data.keys()))
			parameters = step_data[action_name]
			action = WorkflowAction(action_name=action_name, parameters=parameters or {})
			self.raw_actions.append(action)
