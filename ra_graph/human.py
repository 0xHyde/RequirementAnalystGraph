import chainlit as cl
from chainlit.sync import run_sync
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_core.messages import HumanMessage

load_dotenv()


@tool
def human(question: str):
    """此工具对于与用户交谈非常有用"""

    message = run_sync(cl.AskUserMessage(content=question, timeout=1800).send())

    if message is None:
        message = {"output":"用户没有回答此问题"}

    messages = {
        "messages": [HumanMessage("用户：" + message["output"])],
        "sender": "user"
    }

    return messages


user_input = {
    "question": lambda x: x["messages"][-1].content
}

chain_user = user_input | human
