import asyncio
import os
import json
from typing import List, Optional, Tuple

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, SecretStr, Field

from browser_use import Agent, Browser,BrowserConfig

from dotenv import load_dotenv

from browser_use.controller.service import Controller

load_dotenv()

api_key_openrouter = os.getenv('OPENROUTER_API_KEY', '')
if not api_key_openrouter:
    raise ValueError('OPENROUTER_API_KEY is not set')


def init_browser():
    browser = Browser(
        config=BrowserConfig(
            browser_binary_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',  # macOS path
        )
    )
    return browser

def init_llm() -> Tuple[ChatOpenAI, ChatOpenAI]:
    plan_llm = ChatOpenAI(
        base_url='https://api.seeknow.org/openrouter/api/v1',
        # model='openai/gpt-4.1',
        model='google/gemini-2.5-flash-preview:thinking',
        # model="google/gemini-2.5-flash-preview",
        api_key=SecretStr(api_key_openrouter),
        temperature=0.2
    )
    llm = ChatOpenAI(
        base_url='https://api.seeknow.org/openrouter/api/v1',
        # model='openai/gpt-4.1',
        model="google/gemini-2.5-flash-preview",
        api_key=SecretStr(api_key_openrouter),
        temperature=0.2
    )
    return plan_llm, llm

controller = Controller()


class Page(BaseModel):
    page_id: str = Field(description="Page ID")
    description: Optional[str] = Field(default=None, description="Page Desc")
    func_redirect_pages: Optional[List["Page"]] = Field(default=None, description="Functional redirect pages")

class Workflow(BaseModel):
    id: str = Field(description="Workflow id")
    name: str = Field(description="Workflow name")
    description: str = Field(description="Workflow description")
    page_flow: Optional[Page] = Field(default=None, description="Tree of pages in workflow")
    
class WorkflowOutput(BaseModel):
    name: str = Field(description="Website name")
    data: List[Workflow] = Field(default=[], description="List of workflows")
    

@controller.action('save workflow', param_model=WorkflowOutput)
def save_workflow(params: WorkflowOutput):
    with open('workflow.json', 'a') as f:
        json.dump(params.data, f)


async def run_agent(task: str, max_steps: int = 38):
    browser = init_browser()
    plan_llm, llm = init_llm()
    
    agent = Agent(task=task, planner_llm=plan_llm, llm=llm, use_vision=False, browser=browser, controller=controller)
    result = await agent.run(max_steps=max_steps)
    return result 



if __name__ == "__main__":
    urls = [
        # {
        #     "url":"https://www.baidu.com/",
        #     "type":"Search Website",
        #     "name":"baidu"
        # },
        # {
        #     "url":"https://www.tailopez.com/",
        #     "type":"Branding Or Biography Website",
        #     "name":"tailopez"
        # },
        {
            "url":"https://www.mayaangelou.com/",
            "type":"Branding Or Biography Website",
            "name":"mayaangelou"
        },
        # {
        #     "url":"https://simonsinek.com/",
        #     "type":"Branding Or Biography Website",
        #     "name":"simonsinek"
        # }
    ]
    for item in urls:
        task = f"""
open website {item["name"]}: `{item["url"]}`, this website is a {item["type"]},
analyze the landing page of the website, find all reachable pages, and output the workflow.
workflow, is the path that users use the main function of the website, including the page jump relationship and the function process in the page.
a website may have many workflows, each workflow corresponds to a main function.
a website's one workflow is composed of the following parts:
- "id": "short workflow id"
- "name": "Name of the workflow."
- "description": "Detailed description of the workflow."
- "page_flow": Tree of page for the workflow, where each page contains:
    - "page_id": "id of page"
    - "description": "Briefly describe the functionalities of the page related to the workflow, additionally, describe under what circumstances this page is accessed (only within the current workflow, the pages above this page), and what next pages can be accessed from it (only within the current workflow, the pages below this page)"
    - "func_redirect_pages": List of functional redirect pages, which is the page that can be accessed from the current page, and the page is the main function of the workflow.
    
an example of a workflow:
    {{
        "id":"register",
        "name":"register",
        "description":"user register",
        "page_flow":[
            {{
                "page_id":"home_page",
                "description":"has register button, click it to enter the register page"
                "func_redirect_pages":[
                    {{
                        "page_id":"register_page",
                        "description":"Redirected from click register button on home page, has register form, fill in the registration information and submit, if valid, enter the register success page, if invalid, enter the register failed page"
                        "func_redirect_pages":[
                            {{
                                "page_id":"register_success_page",
                                "description":"Redirected from register_page after successful registration, displays a success message and automatically redirects to home page after a countdown timer"
                                "func_redirect_pages":[]
                            }},
                            {{
                                "page_id":"register_failed_page",
                                "description":"Redirected from register_page after failed registration, displays an error message and provides a button to return to the register page to try again",
                                "func_redirect_pages":[]
                            }}
                        ]
                    }}
                ]
            }}
        ]
    }}
First, analyze the homepage to identify all possible workflows. Then, for each identified workflow, systematically explore and document it.
Simulate user interactions to explore and document each workflow of the website, recording the following details for each interaction path:
- the type and position of the interactive element
- the input the user needs to provide (if any), only fill in functionality-related forms, for contact information or similar forms, just pass
- the system response and page changes
- possible branch paths or options
- my browser is already logged in to google, so when I encounter a login requirement, I directly select google login, using my first google account


Explore the main paths of the core functionality, focusing on depth rather than breadth. You don't need to explore every possible path, but dive deeply into the primary workflows. Stay within the website's domain and don't navigate away from the site. Focus on documenting the key user journeys through the main functionality in detail.

For each workflow, document the sequence of pages a user encounters when using the main functionality, including main possible branches and outcomes.
Special emphasis:In some cases, the website may require private information or need to pay or other conditions, skip it, assume success and then infer the subsequent success pages. Remember, your goal is to understand the website's workflow design, not to complete a specific task
"""
        asyncio.run(run_agent(task))