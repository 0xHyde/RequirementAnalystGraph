import sys

sys.path.append("../")
from dotenv import find_dotenv, load_dotenv

_ = load_dotenv(find_dotenv())

import chainlit as cl
from ra_graph.ra_graph import get_ra_graph


@cl.on_chat_start
def start():
    graph = get_ra_graph()
    cl.user_session.set("graph", graph)


@cl.on_message
async def main(message: cl.Message):
    graph = cl.user_session.get("graph")
    async for s in graph.astream(
            message.content, {"recursion_limit": 1000}
    ):
        if "__end__" not in s:
            if "supervisor" in s:
                res = "To " + s["supervisor"]["Next"] + "\n### 任务：\n" + s["supervisor"]["task"] + "\n### 要求：\n" + \
                      s["supervisor"]["requirements"]
                # await cl.Message(content=res).send()
                async with cl.Step(name="AI思考") as step:
                    step.output = res
                    await step.update()
            elif "analyst" in s:
                if s["analyst"]["Next"] != "user":
                    res = "To " + s["analyst"]["Next"] + "\n" + s["analyst"]["messages"][-1].content
                    # await cl.Message(content=res).send()
                    async with cl.Step(name="AI思考") as step:
                        step.output = res
                        await step.update()
            elif "reviewer" in s:
                res = "To supervisor\n" + s["analyst"]["messages"][-1].content
                # await cl.Message(content=res).send()
                async with cl.Step(name="AI思考") as step:
                    step.output = res
                    await step.update()
            elif "expert" in s:
                res = "To analyst\n" + s["analyst"]["messages"][-1].content
                # await cl.Message(content=res).send()
                async with cl.Step(name="AI思考") as step:
                    step.output = res
                    await step.update()

