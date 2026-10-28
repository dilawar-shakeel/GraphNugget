"""LangGraph workflow for the Discord bot.

Every owner message goes through a decision node (OpenAI Decisions API, gpt-6-luna) that decides
whether it is a job post. Job posts go to the job_post node; everything else continues as
a normal chat with memory.

    python -m graphnugget.workflow                 run the bot
    python -m graphnugget.workflow --draw          render graph.png (and graph.mmd) and open it
"""

import asyncio
import logging
import sys
from typing import Annotated, Literal, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from graphnugget import discord_boy

import io
from PIL import Image

def open_graph_window(app) -> None:
    """Takes a compiled LangGraph app and opens its visual structure in a separate window."""
    try:
        # 1. Get the graph image bytes
        png_bytes = app.get_graph().draw_mermaid_png()
        
        # 2. Convert bytes into an image object
        image = Image.open(io.BytesIO(png_bytes))
        
        # 3. Open the image in the system's default image viewer window
        image.show()
        
    except Exception as e:
        print(f"Error opening graph window: {e}")
        print("Tip: Ensure you have PIL installed: 'pip install pillow'")


load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("graphnugget.workflow")

MODEL = "gpt-4o-mini"
THREAD = {"configurable": {"thread_id": "owner"}}

DECISION_MODEL = "gpt-6-luna"
JOB_POST_QUESTION = {
    "type": "predicate",
    "name": "is_job_post",
    "instructions": (
        "Is the message itself a job post: a job listing, vacancy or hiring announcement "
        "(role, requirements, company, apply details)? Questions about jobs, resumes or "
        "casual conversation are NOT job posts."
    ),
}
JOB_POST_THRESHOLD = 0.5
CHAT_PROMPT = "You are a helpful assistant chatting with your owner on Discord. Be concise."


class State(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    is_job_post: bool
    reply: str


_llm = ChatOpenAI(model=MODEL, temperature=0, timeout=30, max_retries=3)
_openai = AsyncOpenAI(timeout=30, max_retries=3)


async def decide(state: State) -> State:
    text = state["messages"][-1].content
    result = await _openai.decisions.create(
        model=DECISION_MODEL, input=text, questions=[JOB_POST_QUESTION]
    )
    answer = result.answers[0]
    if answer.type != "predicate":  # refusal: fall back to normal chat
        log.warning("decision refused: %s", answer.type)
        return {"is_job_post": False}
    log.info("is_job_post probability=%.2f", answer.probability)
    return {"is_job_post": answer.probability >= JOB_POST_THRESHOLD}


def route(state: State) -> Literal["job_post", "chat"]:
    return "job_post" if state["is_job_post"] else "chat"


async def job_post(state: State) -> State:
    # Placeholder: job post handling goes here.
    return {"reply": "Job post detected."}


async def chat(state: State) -> State:
    reply = await _llm.ainvoke([SystemMessage(CHAT_PROMPT), *state["messages"]])
    return {"messages": [reply], "reply": reply.content}


def build_graph(checkpointer=None):
    g = StateGraph(State)
    g.add_node("decide", decide)
    g.add_node("job_post", job_post)
    g.add_node("chat", chat)
    g.add_edge(START, "decide")
    g.add_conditional_edges("decide", route, {"job_post": "job_post", "chat": "chat"})
    g.add_edge("job_post", END)
    g.add_edge("chat", END)
    return g.compile(checkpointer=checkpointer)


async def chat_loop() -> None:
    app = build_graph(MemorySaver())
    open_graph_window(app)
    while True:
        text = await discord_boy.read_message()
        try:
            result = await app.ainvoke({"messages": [HumanMessage(text)]}, THREAD)
            await discord_boy.send_message(result["reply"])
        except Exception:
            log.exception("workflow failed")
            await discord_boy.send_message("Something went wrong handling that message.")


async def main() -> None:
    tasks = [asyncio.create_task(discord_boy.start()), asyncio.create_task(chat_loop())]
    try:
        await asyncio.gather(*tasks)
    finally:
        for t in tasks:
            t.cancel()


if __name__ == "__main__":
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            pass
