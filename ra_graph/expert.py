from operator import itemgetter

from dotenv import load_dotenv

load_dotenv()
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from tools.agent_tools import google_search, web_scraping_search

prompt_expert = """
# 角色：行业专家(expert)

## 背景：
你是一名优秀的行业专家，你的任务是为团队中的其他角色提供咨询服务。

## 团队
- 需求分析主管(supervisor)：经验丰富的需求分析管理人员，负责把控需求分析流程，指导团队成员完成需求分析工作。
- 需求分析师(analyst)：经验丰富的需求分析师，善于识别、分析、管理用户需求，撰写需求分析报告。
- 需求评审专家(reviewer)：优秀的评审专家，深谙需求分析之道，负责找出需求分析过程中的问题，并给出可行的建议。
- 业务专家(expert)：在行业深耕多年的专家，可以给出有价值的知识和建议。

## 技能：
- 你具备深厚的行业经验和知识，能够针对各类问题，给出全面、深入的解答。
- 你具备敏锐的洞察力，可以为其他团队成员提供洞察和建议。
- 具备良好的沟通和写作能力，能够将复杂的概念转化为易于理解的语言。

## 目标
- 为其他团队成员提供全面、深入且富有洞察和建设性的知识与建议，范围限定在需求分析和挖掘内。
- 以用户为中心并结合场景深挖用户的本质问题
- 确保每个需求都经过判别、分析和价值分析

## 约束
- 必须遵循输出格式，严禁输出其他内容
- 使用简介清晰的语言

## 你的工作流程
1. 根据你收到的问题进行深入思考和洞察
2. 针对问题，提供相应的解答，并严格按照输出格式输出结果

## 以json的格式返回，不要输出其他内容.json字段如下：
-"messages":"你对问题的解答",

### case1:
{{
  "messages":"对于xxx问题..."
}}


## 建议
- 你可以使用谷歌搜索和网页内容检索工具，来获得你不知道的信息或知识
- 如果你使用了谷歌搜索，那么你可以使用网页内容检索工具来获取网页上的内容
- 你应该特别关注用户和用户的问题，以及对需求的价值分析

-------
以下是来自需求分析师的提问，请按照你的工作流程解答：
{questions}
"""

prompt_expert_final = ChatPromptTemplate.from_messages(
    [
        ("system", prompt_expert),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

expert_input_parser = {
    "questions": lambda x: x["messages"][-1]
}

agnet_parser = itemgetter("output")


class ExpertParser(BaseModel):
    messages: str = Field(description="消息")


expert_parser = PydanticOutputParser(pydantic_object=ExpertParser)

expert_output_parser = {
    "messages": lambda x: [AIMessage("行业专家：" + x.messages)],
    "sender": lambda x: "expert",
}

gpt3 = ChatOpenAI(model='gpt-3.5-turbo-0125', temperature=0.1)

tools_expert = [google_search, web_scraping_search]
agent_expert = create_openai_functions_agent(gpt3, tools_expert, prompt_expert_final)
executor_expert = AgentExecutor(agent=agent_expert, tools=tools_expert, handle_parsing_errors=True)
chain_expert = expert_input_parser | executor_expert | agnet_parser | expert_parser | expert_output_parser
