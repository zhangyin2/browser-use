import asyncio
import os
from dataclasses import dataclass
from typing import List, Optional

# Third-party imports
import gradio as gr
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Local module imports
from browser_use import Agent, Browser, BrowserConfig

load_dotenv()


@dataclass
class ActionResult:
	is_done: bool
	extracted_content: Optional[str]
	error: Optional[str]
	include_in_memory: bool


@dataclass
class AgentHistoryList:
	all_results: List[ActionResult]
	all_model_outputs: List[dict]


def parse_agent_history(history_str: str) -> None:
	console = Console()

	# Split the content into sections based on ActionResult entries
	sections = history_str.split('ActionResult(')

	for i, section in enumerate(sections[1:], 1):  # Skip first empty section
		# Extract relevant information
		content = ''
		if 'extracted_content=' in section:
			content = section.split('extracted_content=')[1].split(',')[0].strip("'")

		if content:
			header = Text(f'Step {i}', style='bold blue')
			panel = Panel(content, title=header, border_style='blue')
			console.print(panel)
			console.print()


async def run_browser_task(
	task: str,
	model: str = 'gpt-4o',
	temperature: float = 0.2,
	headless: bool = True,
	use_vision: bool = True,
) -> str:
    
	api_key = os.getenv('OPENROUTER_API_KEY', "")

	try:
		agent = Agent(
			task=task,
			llm=ChatOpenAI(model=model, 
                  	base_url='https://openrouter.ai/api/v1', 
                  	temperature=temperature,
                  	api_key=SecretStr(api_key) if api_key else None),
			browser=Browser(config=BrowserConfig(browser_binary_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')),
			use_vision=use_vision,
		)
		result = await agent.run()
		# 将 AgentHistoryList 转换为字符串
		if isinstance(result, AgentHistoryList):
			parse_agent_history(str(result))
			return str(result)
		return result
	except Exception as e:
		return f'Error: {str(e)}'


def create_ui():
	with gr.Blocks(title='Browser Use GUI') as interface:
		gr.Markdown('# Browser Use Task Automation')

		with gr.Row():
			with gr.Column():
       
				task = gr.Textbox(
					label='Task Description',
					placeholder='E.g., Find flights from New York to London for next week',
					lines=3,
				)
				model = gr.Dropdown(choices=['deepseek/deepseek-chat-v3-0324','openai/gpt-4.1', 'openai/o4-mini-high'], label='Model', value='openai/gpt-4.1')
				temperature = gr.Slider(minimum=0, maximum=1, step=0.1, value=0.5, label='Temperature')
				headless = gr.Checkbox(label='Run Headless', value=True)
				use_vision = gr.Checkbox(label='Use Vision', value=True)
				submit_btn = gr.Button('Run Task')

			with gr.Column():
				output = gr.Textbox(label='Output', lines=10, interactive=False)

		submit_btn.click(
			fn=lambda *args: asyncio.run(run_browser_task(*args)),
			inputs=[task, model, temperature, headless, use_vision],
			outputs=output,
		)

	return interface


if __name__ == '__main__':
	demo = create_ui()
	demo.launch()
