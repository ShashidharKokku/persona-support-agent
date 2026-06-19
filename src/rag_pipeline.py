
"""
rag_pipeline.py — Document ingestion, embedding, and semantic retrieval.
"""
 
import os
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from google import genai
import chromadb
 
from src.config import (
    GEMINI_API_KEY, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_RESULTS,
    CHROMA_DB_DIR, COLLECTION_NAME, DATA_DIR
)
 
EMBEDDING_MODEL = "gemini-embedding-001"
 
 
class LocalRAGPipeline:
    def __init__(self):
        self.genai_client   = genai.Client(api_key=GEMINI_API_KEY)
        self.chroma_client  = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        self.collection     = self.chroma_client.get_or_create_collection(
                                  name=COLLECTION_NAME,
                                  metadata={"hnsw:space": "cosine"}
                              )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
 
    def get_embedding(self, text: str) -> list:
        """Convert text into a Gemini embedding vector."""
        result = self.genai_client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text
        )
        return result.embeddings[0].values
 
    def _read_file(self, filepath: str) -> str:
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".pdf":
            reader = PdfReader(filepath)
            return "\n".join(
                page.extract_text() for page in reader.pages if page.extract_text()
            )
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
 
    def ingest_document(self, doc_name: str, content: str):
        chunks = self.splitter.split_text(content)
        for idx, chunk in enumerate(chunks):
            chunk_id  = f"{doc_name}_chunk_{idx}"
            embedding = self.get_embedding(chunk)
            self.collection.upsert(
                ids=[chunk_id],
                embeddings=[embedding],
                metadatas=[{"source": doc_name, "chunk_index": idx}],
                documents=[chunk]
            )
 
    def load_all_documents(self, force_reload: bool = False):
        existing_count = self.collection.count()
        if existing_count > 0 and not force_reload:
            print(f"[RAG] Already loaded ({existing_count} chunks). Skipping.")
            return
 
        supported = (".txt", ".md", ".pdf")
        files_loaded = 0
        for filename in os.listdir(DATA_DIR):
            if not filename.endswith(supported):
                continue
            filepath = os.path.join(DATA_DIR, filename)
            print(f"[RAG] Ingesting: {filename}")
            content = self._read_file(filepath)
            self.ingest_document(doc_name=filename, content=content)
            files_loaded += 1
 
        print(f"[RAG] Done! {files_loaded} file(s) → {self.collection.count()} chunks indexed.")
 
    def retrieve_context(self, query: str, top_k: int = TOP_K_RESULTS) -> list:
        if self.collection.count() == 0:
            return []
 
        query_vector = self.get_embedding(query)
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=min(top_k, self.collection.count())
        )
 
        retrieved = []
        if results and results["documents"]:
            for i in range(len(results["documents"][0])):
                distance = results["distances"][0][i] if results.get("distances") else 0.0
                score    = round(1.0 - distance / 2.0, 4)
                retrieved.append({
                    "text":   results["documents"][0][i],
                    "source": results["metadatas"][0][i]["source"],
                    "score":  score
                })
        return retrieved