"""End-to-end agent tests. Needs a real OPENAI_API_KEY (and, for the MCP
case, the calculator MCP server reachable) — run with `pytest -m integration`.
"""
import pytest
from langchain_core.messages import HumanMessage

pytestmark = pytest.mark.integration


async def test_agent_answers_a_plain_question(require_real_openai_key):
    from graph import build_graph

    chatbot = await build_graph()
    result = await chatbot.ainvoke(
        {"messages": [HumanMessage(content="Reply with exactly one word: banana.")]},
        config={"configurable": {"thread_id": "it-plain"}},
    )
    assert "banana" in result["messages"][-1].content.lower()


async def test_agent_uses_a_local_tool(require_real_openai_key):
    from graph import build_graph

    chatbot = await build_graph()
    result = await chatbot.ainvoke(
        {"messages": [HumanMessage(content="Use a tool to multiply 12 and 12.")]},
        config={"configurable": {"thread_id": "it-tool"}},
    )
    assert "144" in result["messages"][-1].content


def _make_minimal_pdf(text: str) -> bytes:
    """A minimal, structurally valid single-page PDF containing `text`."""
    content = f"BT /F1 12 Tf 20 100 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(content)} >>\nstream\n".encode() + content + b"\nendstream",
    ]
    pdf = b"%PDF-1.4\n"
    offsets = []
    for i, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_pos = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        pdf += f"{off:010d} 00000 n \n".encode()
    pdf += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode()
    pdf += f"startxref\n{xref_pos}\n%%EOF".encode()
    return pdf


async def test_agent_ingests_and_searches_a_pdf(require_real_openai_key):
    from graph import build_graph
    from tools.pdf import ingest_pdf_bytes

    pdf_bytes = _make_minimal_pdf("The secret code is 4271.")
    summary = ingest_pdf_bytes(pdf_bytes, "secret.pdf")
    assert summary.get("pages") == 1

    chatbot = await build_graph()
    result = await chatbot.ainvoke(
        {"messages": [HumanMessage(content="What is the secret code in the document?")]},
        config={"configurable": {"thread_id": "it-pdf"}},
    )
    assert "4271" in result["messages"][-1].content
