# backend.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # make src/ importable

import config  # noqa: E402,F401  -- imported for side effect: loads .env
from langchain_core.messages import HumanMessage  # noqa: E402
from graph import build_graph, get_checkpointer  # noqa: E402
import asyncio  # noqa: E402
import threading  # noqa: E402
import queue  # noqa: E402

# Dedicated async loop for backend tasks
_ASYNC_LOOP = asyncio.new_event_loop()
_ASYNC_THREAD = threading.Thread(target=_ASYNC_LOOP.run_forever, daemon=True)
_ASYNC_THREAD.start()

def _submit_async(coro):
    return asyncio.run_coroutine_threadsafe(coro, _ASYNC_LOOP)


def run_async(coro):
    return _submit_async(coro).result()


def submit_async_task(coro):
    """Schedule a coroutine on the backend event loop."""
    return _submit_async(coro)


checkpointer = run_async(get_checkpointer())

# Module-level graph so importers (e.g. streamlit_frontend) can use it directly
chatbot = run_async(build_graph())


async def _alist_threads():
    all_threads = set()
    async for checkpoint in checkpointer.alist(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])
    return list(all_threads)


def retrieve_all_threads():
    return run_async(_alist_threads())


def get_conversation(thread_id):
    """Return the stored message history for a thread (sync wrapper)."""
    state = run_async(
        chatbot.aget_state({"configurable": {"thread_id": thread_id}})
    )
    return state.values.get("messages", []) if state else []


def stream_chat(messages, run_config):
    """
    Drive chatbot.astream(...) on the backend event loop and yield chunks
    synchronously, so Streamlit can consume it with st.write_stream.
    Yields (message_chunk, metadata) tuples (stream_mode="messages").
    """
    q: "queue.Queue" = queue.Queue()
    sentinel = object()

    async def _producer():
        try:
            async for chunk in chatbot.astream(
                {"messages": messages}, config=run_config, stream_mode="messages"
            ):
                q.put(chunk)
        except Exception as e:  # forward the error to the consumer
            q.put(e)
        finally:
            q.put(sentinel)

    submit_async_task(_producer())

    while True:
        item = q.get()
        if item is sentinel:
            break
        if isinstance(item, Exception):
            raise item
        yield item

async def main():
    result = await chatbot.ainvoke(
        {"messages": [HumanMessage(content="Find the modulus of 132354 and 23 and give answer like a cricket commentator.")]},
        config={"configurable": {"thread_id": "main-thread"}},
    )
    print("Chatbot is ready.")
    print(result['messages'][-1].content)

if __name__ == "__main__":
    asyncio.run(main())