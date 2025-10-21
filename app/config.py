import os


class Config:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    # Database
    DB_URL = os.getenv("DB_URL", "sqlite:///rag.db")
    SQLALCHEMY_DATABASE_URI = DB_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Ollama / Models
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    CHAT_MODEL = os.getenv("CHAT_MODEL", "llama3.1")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

    # Vector Store
    VECTOR_STORE = os.getenv("VECTOR_STORE", "faiss")  # faiss | qdrant (future)

    # API / App
    MAX_INPUT_CHARS = int(os.getenv("MAX_INPUT_CHARS", "8000"))


