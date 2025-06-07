"""
Configuration settings for the Slack RAG Bot
"""

import os


class Config:
    """Configuration class for all settings"""

    # API Keys
    GOOGLE_API_KEY = "your-gemini-api-key"
    SLACK_BOT_TOKEN = "xoxb-your-bot-token"
    SLACK_APP_TOKEN = "xapp-your-app-token"

    # Document paths
    DOCUMENT_PATHS = {
        "Company Culture": "documents/CompanyCulture.pdf",
        "Company Policies": "documents/CompanyPolicies.pdf",
    }

    # Database configuration
    PERSIST_DIRECTORY = "document_db"

    # AI Model settings
    EMBEDDING_MODEL = "models/embedding-001"
    LLM_MODEL = "gemini-2.0-flash"
    LLM_TEMPERATURE = 0.3

    # Text processing settings
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    RETRIEVAL_K = 3

    # Conversation settings
    MAX_HISTORY_LENGTH = 10
    MAX_CHANNEL_MESSAGES = 200

    @classmethod
    def setup_environment(cls):
        """Setup environment variables"""
        os.environ["GOOGLE_API_KEY"] = cls.GOOGLE_API_KEY
        os.environ["SLACK_BOT_TOKEN"] = cls.SLACK_BOT_TOKEN
        os.environ["SLACK_APP_TOKEN"] = cls.SLACK_APP_TOKEN

        # Create persist directory
        os.makedirs(cls.PERSIST_DIRECTORY, exist_ok=True)

    @classmethod
    def validate_config(cls):
        """Validate configuration settings"""
        required_fields = ["GOOGLE_API_KEY", "SLACK_BOT_TOKEN", "SLACK_APP_TOKEN"]

        for field in required_fields:
            if not getattr(cls, field):
                raise ValueError(f"Missing required configuration: {field}")

        # Check if document paths exist
        missing_docs = []
        for name, path in cls.DOCUMENT_PATHS.items():
            if not os.path.exists(path):
                missing_docs.append(f"{name}: {path}")

        if missing_docs:
            print(f"⚠️  Warning: Missing documents:")
            for doc in missing_docs:
                print(f"   - {doc}")

        return len(missing_docs) == 0
