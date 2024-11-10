from asyncio import run

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from browser_use import Agent

load_dotenv()

llm = ChatOpenAI(model='gpt-4o', temperature=0)

task = 'Go to hackernews, click through the categories and '
task += 'give me the top 2 posts for each category like news, past, show hn ect. '
task += 'Calculate for each the ratio of points per hour. '
task += 'This format: <category>: Title: <title>, Points: <points>, Hours: <hours>, Ratio: <ratio>'

agent = Agent(task=task, llm=llm)

run(agent.run())

# run with: python -m examples.hn_search
