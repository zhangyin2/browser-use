import asyncio
import os
import json
from typing import List, Optional, Tuple
import pandas as pd  # 添加 pandas 导入

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, SecretStr, Field

from browser_use import Agent, Browser,BrowserConfig

from dotenv import load_dotenv

from browser_use.controller.service import Controller

load_dotenv()

api_key_openrouter = os.getenv('OPENROUTER_API_KEY', '')
if not api_key_openrouter:
    raise ValueError('OPENROUTER_API_KEY is not set')

browser_context = None
async def init_browser_context():
    global browser_context
    if browser_context is None:
        browser = Browser(
            config=BrowserConfig(
                browser_binary_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',  # macOS path
            )
        )
        browser_context = await browser.new_context()
    return browser_context

def init_llm() -> Tuple[ChatOpenAI, ChatOpenAI, ChatOpenAI]:
    plan_llm = ChatOpenAI(
        base_url='https://api.seeknow.org/openrouter/api/v1',
        # model='openai/gpt-4.1',
        model='google/gemini-2.5-flash-preview:thinking',
        # model='openai/o4-mini-high',
        # model="google/gemini-2.5-flash-preview",
        api_key=SecretStr(api_key_openrouter),
        temperature=0.1
    )
    llm = ChatOpenAI(
        base_url='https://api.seeknow.org/openrouter/api/v1',
        # model='openai/gpt-4.1',
        # model="openai/gpt-4.1-mini",
        model='openai/o4-mini',
        api_key=SecretStr(api_key_openrouter),
        temperature=0.1
    )
    extractor_llm = ChatOpenAI(
        base_url='https://api.seeknow.org/openrouter/api/v1',
        model='openai/gpt-4.1-mini',
        api_key=SecretStr(api_key_openrouter),
        temperature=0.1
    )
    return plan_llm, llm, extractor_llm

controller = Controller()

class Transition(BaseModel):
    to_page: str = Field(description="To page id")
    description: Optional[str] = Field(default=None, description="Transition description")


class Page(BaseModel):
    page_id: str = Field(description="Page ID")
    title: Optional[str] = Field(default=None, description="Page Title")
    description: Optional[str] = Field(default=None, description="Page Desc")
    specification: Optional[List[str]] = Field(default=None, description="Page Specification")
    transitions: Optional[List[Transition]] = Field(default=None, description="Transitions from current page to next page")
    external_links: Optional[List[Transition]] = Field(default=None, description="External links from current page to external website")

    
class Pageflow(BaseModel):
    site_name: str
    page: List[Page]
    

@controller.action('Save pageflow to file', param_model=Pageflow)
def save_pageflow_to_file(params: Pageflow):
    with open(f'pageflow_{params.site_name.replace(" ", "_")}.jsonl', 'a') as f:
        for page in params.page:
            f.write(json.dumps(page.model_dump(), ensure_ascii=False) + '\n')


async def run_agent(task: str, max_steps: int = 38, initial_actions: List[dict] = []):
    plan_llm, llm, extractor_llm = init_llm()
    context = await init_browser_context()
    agent = Agent(task=task, initial_actions=initial_actions, planner_llm=plan_llm, llm=llm, 
                page_extraction_llm=extractor_llm, is_planner_reasoning=True, 
                enable_memory=False, use_vision=False, browser_context=context, controller=controller)
    result = await agent.run(max_steps=max_steps)
    return result 

def read_url_items_from_csv(path: str) -> List[dict] | None:
    """
    Read URL items from an CSV file.

    Args:
        path: The path to the CSV file.

    Returns:
        A list of dictionaries, where each dictionary contains 'type', 'name', 'url' and 'has_done'
        extracted from columns 0, 1, 2, 3 respectively. Returns None if the file
        cannot be read or does not exist.
    """
    try:
        # 读取 Excel 文件，假设没有表头，只读取第 0, 1, 2, 3 列
        df = pd.read_csv(path, header=None, usecols=[0, 1, 2, 3])
        # 重命名列
        df.columns = ['type', 'name', 'url', 'has_done']
        # 转换为字典列表
        result = df.to_dict('records')
        return result
    except FileNotFoundError:
        print(f"Error: File not found at {path}")
        return None
    except Exception as e:
        print(f"Error reading Excel file {path}: {e}")
        return None
    
def finish_task(file_path: str, name: str):
    df = pd.read_csv(file_path, header=None, usecols=[0, 1, 2, 3])
    df.loc[df[1] == name, 3] = 1
    df.to_csv(file_path, index=False)


if __name__ == "__main__":
    # urls = [
    #     {
    #         "url":"https://www.tailopez.com/",
    #         "type":"Branding Or Biography Website",
    #         "name":"tailopez"
    #     },
    #     {
    #         "url":"https://www.mayaangelou.com/",
    #         "type":"Branding Or Biography Website",
    #         "name":"mayaangelou"
    #     },
    #     {
    #         "url":"https://simonsinek.com/",
    #         "type":"Branding Or Biography Website",
    #         "name":"simonsinek"
    #     },
    # ]
    # 示例：从文件读取（如果需要）
    file_path = '/Users/zhangyin/Downloads/webs.csv'
    url_items_from_file = read_url_items_from_csv(file_path)
    if url_items_from_file:
        urls = url_items_from_file

    for item in urls:
        if item["has_done"] == 1:
            print(f"pass {item['name']}")
            continue
        print(f"start {item['name']}")
        initial_actions = [
            {'go_to_url': {'url': item["url"]}}
        ]
        task = f"""
Explore a website's pageflow, and save the pageflow to the file.
1. Open website {item["name"]}: `{item["url"]}`, this website is a {item["type"]},
2. You should analyze the homepage to identify all possible transitions. Simulate user interactions to explore and document each page of the website, recording the following details for each transition:
- the type of the interactive element
- the input the user needs to provide (if any), only fill in functionality-related forms, for contact information or similar forms, just pass
- the system response and page changes
- possible branch paths or options
3. if the page has repeated elements(like pagination, list, etc.), you just explore the first one.
4. Organize all pages into a pageflow structure.
5. save the pageflow to the file.

pageflow, is the path that users use the main function of the website, including the page jump relationship and the function process in the page.
a website may have many pages, each page has a page_id, and a description of the page, and the transitions to other pages.
a website's one page is composed of the following parts:
    - "page_id": "id of page"
    - "title": "title of the page"
    - "description": "Briefly describe the functionalities of the page related to the website"
    - "specification": "List of specifications of the page, including the elements in the page, the layout of the page, the interactive elements in the page, the input the user needs to provide (if any), the system response and page changes, possible branch paths or options"
    - "transitions": List of transitions, which is the page that can be accessed from the current page, and the page is the main function of the website.
        - "to_page": "id of the next page, must not be the current page"
        - "description": "Briefly describe how to enter the next page from the current page"
    - "external_links": List of external links, which is the external website that can be accessed from the current page, has the same structure as transitions.
example page:
```json
    {{
        "page_id":"home_page",
        "description":"the home page of the website, show the logo, the main function of the website, and the navigation bar",
        "specification":[
            "in header, Main navigation links: Home, About, Services, Contact, Blog, Login, Register",
            "a hero section about the website",
            "a example list section, each item in the list has a title, a description, a image, a link to the detail page",
            "in the footer, there is a copyright section and social media icons"
        ],
        "transitions":[
            {{
                "to_page":"register_page",
                "description":"click register link"
            }},
            {{
                "to_page":"login_page",
                "description":"click login link"
            }},
            {{
                "to_page":"about_page",
                "description":"click about link"
            }},
            {{
                "to_page":"example_detail_page",
                "description":"click one item in example list section"
            }},
            {{
                "to_page":"contact_page",
                "description":"click contact link"
            }},
            ...
        ],
        "external_links":[
            {{
                "to_page":"youtube_watch_page",
                "description":"navigate to youtube watch page by clicking youtube video in the hero section"
            }},
            {{
                "to_page":"facebook_page",
                "description":"navigate to facebook page by clicking facebook link in the footer"
            }},
            ...
        ]
    }}
```

My browser is already logged in to google, so when I encounter a login requirement, I directly select google login, using my first google account

If a transition points to an external website, only record the external_links to the external website, don't navigate to the external website.
Stay within the website's domain and don't navigate away from the site. Focus on documenting user journeys through the pageflow.

Special emphasis:In some cases, the website may require private information or need to pay or other conditions, skip it, assume success and then infer the subsequent success pages. Remember, your goal is to document the website's pageflow design and save the pageflow to the file.
"""
# In the end, output the main workflows based on the pageflow. Workflow is the main function of the website, which is the path that users use the main function of the website.
    
        asyncio.run(run_agent(task, max_steps=400, initial_actions=initial_actions))
        finish_task(file_path, item["name"])