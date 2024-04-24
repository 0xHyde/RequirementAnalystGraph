# 定义图状态
import operator
from typing import TypedDict, Annotated, List

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, AIMessage

load_dotenv()
from ra_graph.analyst import chain_analyst
from ra_graph.expert import chain_expert
from ra_graph.human import chain_user
from ra_graph.reviewer import chain_reviewer
from ra_graph.supervisor import chain_supervisor


class RATeamState(TypedDict):
    # 消息历史
    messages: Annotated[List[BaseMessage], operator.add]
    # 下一角色
    Next: str
    # 任务
    task: str
    # 要求
    requirements: str
    # 发送人
    sender: str


# 创建图

from langgraph.graph import StateGraph, END

research_graph = StateGraph(RATeamState)

research_graph.add_node("supervisor", chain_supervisor)
research_graph.add_node("analyst", chain_analyst)
research_graph.add_node("reviewer", chain_reviewer)
research_graph.add_node("expert", chain_expert)
research_graph.add_node("user", chain_user)

research_graph.add_conditional_edges(
    "supervisor",
    lambda x: x["Next"],
    {
        "analyst": "analyst",
        "reviewer": "reviewer",
        "FINISH": END
    }
)

research_graph.add_conditional_edges(
    "analyst",
    lambda x: x["Next"],
    {
        "supervisor": "supervisor",
        "user": "user",
        "expert": "expert",
        "analyst": "analyst",
    }
)

research_graph.add_edge("expert", "analyst")
research_graph.add_edge("reviewer", "supervisor")
research_graph.add_edge("user", "analyst")

research_graph.set_entry_point("supervisor")

RATeamChain = research_graph.compile()


def enter_chain(message: str):
    results = {
        "messages": [AIMessage(message)],
    }
    return results


def get_ra_graph():
    return enter_chain | RATeamChain
