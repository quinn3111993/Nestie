"""
Slack RAG Bot - Main Application
A Slack bot that can answer questions using RAG and provide natural conversation capabilities.
"""

import os
import logging
from config import Config
from document_processor import DocumentProcessor
from rag_chatbot import RAGChatbot
from slack_bot import SlackRAGBot
from slack_handlers import create_slack_app

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_system():
    """Initialize the complete RAG system"""
    try:
        logger.info("Initializing RAG system...")
        
        # 1. Initialize document processor
        doc_processor = DocumentProcessor(
            document_paths=Config.DOCUMENT_PATHS,
            persist_directory=Config.PERSIST_DIRECTORY
        )
        
        # 2. Load and process documents
        success = doc_processor.setup_documents()
        if not success:
            logger.error("Failed to setup documents")
            return None, None
            
        # 3. Create RAG chatbot
        rag_chatbot = RAGChatbot(
            vectorstore=doc_processor.vectorstore,
            loaded_documents=doc_processor.loaded_documents
        )
        
        if not rag_chatbot.is_ready:
            logger.error("Failed to initialize RAG chatbot")
            return None, None
            
        logger.info(f"✅ RAG system initialized successfully!")
        logger.info(f"📚 Documents loaded: {', '.join(doc_processor.loaded_documents)}")
        
        return doc_processor, rag_chatbot
        
    except Exception as e:
        logger.error(f"Error initializing system: {e}")
        return None, None

def main():
    """Main application entry point"""
    try:
        logger.info("🚀 Starting Slack RAG Bot...")
        
        # Initialize RAG system
        doc_processor, rag_chatbot = initialize_system()
        
        if not rag_chatbot:
            logger.error("❌ Failed to initialize RAG system. Exiting.")
            return
            
        # Create Slack app and bot
        app = create_slack_app()
        slack_bot = SlackRAGBot(rag_chatbot, app.client)
        
        # Register handlers
        from slack_handlers import register_handlers
        register_handlers(app, slack_bot)
        
        # Start the bot
        logger.info("🤖 Starting Slack bot...")
        logger.info(f"📋 Available documents: {', '.join(rag_chatbot.loaded_documents)}")
        
        from slack_bolt.adapter.socket_mode import SocketModeHandler
        handler = SocketModeHandler(app, Config.SLACK_APP_TOKEN)
        
        logger.info("✅ Slack RAG Bot is running!")
        handler.start()
        
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Error running bot: {e}")

if __name__ == "__main__":
    main()