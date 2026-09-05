import os
import tempfile
from urllib.parse import urlparse

import requests
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

import config

embeddings = OpenAIEmbeddings(model=config.EMBEDDING_MODEL)

# In-memory FAISS index holding every PDF ingested this session.
_PDF_VECTORSTORE: "FAISS | None" = None


def _ingest_pdf(source: str) -> dict:
    """
    Load a PDF from a local path or http(s) URL, split it, embed the chunks and
    add them to the session-wide FAISS index. Returns a summary or {"error": ...}.
    """
    global _PDF_VECTORSTORE

    tmp_path = None
    path = source
    if urlparse(source).scheme in ("http", "https"):
        try:
            resp = requests.get(source, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            return {"error": f"Could not download PDF: {e}"}
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as fh:
            fh.write(resp.content)
            tmp_path = path = fh.name

    try:
        if not os.path.exists(path):
            return {"error": f"PDF not found: {source}"}

        docs = PyPDFLoader(path).load()
        chunks = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""],
        ).split_documents(docs)
        if not chunks:
            return {"error": "No extractable text (scanned or image-only PDF?)."}

        if _PDF_VECTORSTORE is None:
            _PDF_VECTORSTORE = FAISS.from_documents(chunks, embeddings)
        else:
            _PDF_VECTORSTORE.add_documents(chunks)

        return {
            "source": source,
            "pages": len(docs),
            "chunks": len(chunks),
            "characters": sum(len(c.page_content) for c in chunks),
        }
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def ingest_pdf_bytes(file_bytes: bytes, filename: str) -> dict:
    """
    Ingest a PDF from raw bytes (e.g. a browser upload) rather than a path/URL.
    Same effect as `_ingest_pdf`, with the summary's `source` set to `filename`.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as fh:
        fh.write(file_bytes)
        tmp_path = fh.name
    try:
        result = _ingest_pdf(tmp_path)
        if "source" in result:
            result["source"] = filename
        return result
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


@tool
def ingest_pdf(source: str) -> dict:
    """
    Ingest a PDF so its contents can be searched later with `search_pdf`.
    `source` is a local file path or an http(s) URL pointing to a PDF.
    Returns a summary with page and chunk counts, or {"error": ...}.
    """
    return _ingest_pdf(source)


@tool
def search_pdf(query: str, k: int = 4) -> list[dict]:
    """
    Search the text of PDFs already ingested with `ingest_pdf`.
    Returns up to k passages, each with its page number and source.
    If nothing has been ingested yet, ask the user for a PDF and call `ingest_pdf`.
    """
    if _PDF_VECTORSTORE is None:
        return [{"error": "No PDF ingested yet. Call ingest_pdf first."}]
    hits = _PDF_VECTORSTORE.similarity_search(query, k=k)
    return [
        {
            "page": d.metadata.get("page"),
            "source": d.metadata.get("source"),
            "content": d.page_content,
        }
        for d in hits
    ]
