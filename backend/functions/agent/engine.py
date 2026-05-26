import asyncio
import re
import logging

from integrations import FirebaseManager
from langchain_core.messages import HumanMessage

from .tracing import load_langfuse_client_and_handler
from .main_agent import MainAgentGraph


def split_collated_chunk(collated_chunk: str) -> tuple[str, str]:
    match = re.search(r"([.?!])(?=[^.?!]*$)", collated_chunk)

    if match:
        idx = match.end()
        sent = collated_chunk[:idx]
        remainder = collated_chunk[idx:]

    else:
        sent = ""
        remainder = collated_chunk

    return sent, remainder


def process_streaming_chunk(chunk: dict, collated_chunk: str) -> tuple[dict, str]:
    if isinstance(chunk, dict) and chunk.get("type") == "messages":
        data = chunk.get("data") or []
        content = data[0].content if data else ""
        if len(str(content).strip()) > 0 and len(str(content).strip()) < 500:
            collated_chunk += str(content)
            if len(collated_chunk) > 200:
                sent, remainder = split_collated_chunk(collated_chunk)
                return {"type": "chunk", "data": {"chunk": sent}}, remainder
    else:
        # release the remainder
        if len(collated_chunk.strip()) > 0:
            return {"type": "chunk", "data": {"chunk": collated_chunk}}, ""
    return {}, collated_chunk


test = (
    "Do you know any schemes for hawkers in Singapore?"
    "If so, can you find me some that are still open for application?"
    "If not, can you search the web and find some for me?"
)

if __name__ == "__main__":

    async def test_engine():
        firebase_manager = FirebaseManager()
        main_agent_graph = MainAgentGraph(firestore_client=firebase_manager.firestore_client)
        graph = main_agent_graph.graph

        _, langfuse_handler = load_langfuse_client_and_handler()
        thread_id = "test-thread123"

        demo_state = {
            "messages": [
                HumanMessage(
                    content="do u have access to th",
                )
            ],
            "search_history": [],
            "tool_history": [],
            "current_results_json": "",
        }

        pre = await graph.aget_state(config={"configurable": {"thread_id": thread_id}})
        pre_values = getattr(pre, "values", {}) if pre is not None else {}
        pre_messages = pre_values.get("messages", []) if isinstance(pre_values, dict) else []
        logging.info(
            f"Loaded prior messages for thread_id={thread_id}: {len(pre_messages) if isinstance(pre_messages, list) else 0}"
        )

        collated_chunk = ""
        async for chunk in graph.astream(
            demo_state,
            config={
                "callbacks": [langfuse_handler] if langfuse_handler else [],
                "configurable": {"thread_id": thread_id},
            },
            stream_mode=["messages", "custom"],
            version="v2",
        ):
            result, collated_chunk = process_streaming_chunk(chunk, collated_chunk)
            if result:
                print(result)
            if isinstance(chunk, dict) and chunk.get("type") == "custom":
                print(chunk.get("data"))
            if isinstance(chunk, dict) and chunk.get("type") == "updates":
                print("State update:", chunk.get("data"))

        if collated_chunk.strip():
            print({"type": "chunk", "data": {"chunk": collated_chunk}})

        post = await graph.aget_state(config={"configurable": {"thread_id": thread_id}})
        post_values = getattr(post, "values", {}) if post is not None else {}
        post_messages = post_values.get("messages", []) if isinstance(post_values, dict) else []
        logging.info(
            f"Saved messages for thread_id={thread_id}: {len(post_messages) if isinstance(post_messages, list) else 0}"
        )

    asyncio.run(test_engine())
