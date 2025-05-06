from langchain.agents import create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
import os
from services.ai.tools import tools_list
from services.ai import lm_facade
from langchain.agents import AgentExecutor

class BrandAnalyzer:
    """
    A class to analyze a brand based on a given URL using web scraping and web search.
    """
    def __init__(self, lm_facade: lm_facade.LMFacade):
        """
        Initializes the BrandAnalyzer with the OpenAI API key.
        """
        self.lm_facade = lm_facade

    def create_agent(self):
        """
        Creates the tool-calling agent.
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert brand analyst. Given a URL, you will analyze the brand by first using web search to gather relevant information. Your task is to identify and report on:
- The brand name.
- What the brand is generally about (products, services, mission, etc.).
- The primary geographic regions where this brand is relevant.
- The typical users or target audience of this brand.

After you have performed the web search and have the results, synthesize the information to provide a concise final answer addressing all the points above. Structure your final answer clearly.
""",
                ),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )
        tool_ids = [
            tools_list.ToolId.SEARCH,
            tools_list.ToolId.WEB_SCRAPER
        ]
        tools = [self._get_tool_call_func(id) for id in tool_ids]
        agent = create_tool_calling_agent(
            self.lm_facade.get_langchain_llm(), 
            tools, prompt
        )
        executor = AgentExecutor(agent=agent, tools=tools, verbose=False, return_intermediate_steps=False)
        return executor

    def _get_tool_call_func(self, id: tools_list.ToolId):
        return tools_list.get_tool_call(id)

    def analyze_brand(self, url: str) -> list[str]:
        """
        Analyzes the brand based on the given URL using the created agent with Gemini.
        """
        agent = self.create_agent()
        inputs = {"input": f"""Analyze the brand based on this URL: {url}"""}
        response = agent.invoke(inputs)
        return [response["output"]]
