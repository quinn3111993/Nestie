"""
RAG Chatbot module with intelligent query routing and conversation management
"""

import re
import logging
from typing import List, Dict, Optional
from datetime import datetime
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAI
from config import Config

logger = logging.getLogger(__name__)


class RAGChatbot:
    """Intelligent chatbot that handles both RAG queries and general conversation"""

    def __init__(self, vectorstore, loaded_documents: List[str]):
        self.vectorstore = vectorstore
        self.loaded_documents = loaded_documents
        self.is_ready = False

        # Initialize LLM
        Config.setup_environment()
        self.llm = GoogleGenerativeAI(
            model=Config.LLM_MODEL, temperature=Config.LLM_TEMPERATURE
        )

        # Conversation management
        self.conversation_history = []
        self.max_history_length = Config.MAX_HISTORY_LENGTH
        self.last_query_type = None

        # Query classification patterns
        self._setup_classification_patterns()

        # Initialize chains
        self._setup_chains()

    def _setup_classification_patterns(self):
        """Setup patterns for query classification"""
        self.document_keywords = [
            "document",
            "doc",
            "file",
            "paper",
            "text",
            "pdf",
            "summarize",
            "summary",
            "main topic",
            "key points",
            "information",
            "data",
            "content",
            "source",
            "reference",
            "what does",
            "according to",
            "mentioned in",
            "states that",
            "chapter",
            "section",
            "page",
            "paragraph",
            "policy",
            "rule",
        ]

        # Add document names to keywords
        for doc_name in self.loaded_documents:
            self.document_keywords.append(doc_name.lower())

        self.general_patterns = [
            r"\b(hello|hi|hey|good morning|good afternoon|good evening)\b",
            r"\b(how are you|what\'s up|how\'s it going)\b",
            r"\b(thank you|thanks|appreciate)\b",
            r"\b(goodbye|bye|see you|talk to you later)\b",
            r"\b(who are you|what are you|tell me about yourself)\b",
            r"\b(can you help|help me)\b(?!.*\b(document|file|pdf)\b)",
            r"^\s*(yes|no|okay|ok|sure|maybe|perhaps)\s*$",
            r"\b(weather|time|date|joke|story)\b",
        ]

        self.continuation_patterns = [
            r"\b(also|and|furthermore|additionally|moreover)\b",
            r"\b(what about|how about|tell me more)\b",
            r"\b(continue|more|further|elaborate)\b",
            r"\b(that|this|it|they)\b",
            r"^\s*(and|but|however|although|though)\b",
        ]

    def _setup_chains(self):
        """Setup RAG and general conversation chains"""
        try:
            # RAG prompt template
            rag_template = """
You are a helpful assistant with access to company documents.
Use the provided context to answer questions accurately.

Guidelines:
1. Provide clear, accurate answers based on the context
2. Mention source documents when relevant
3. If information isn't found, say "I don't find relevant information in the available documents"
4. Keep responses concise but complete
5. Be conversational and friendly

For Slack formatting:
- Use *text* for bold (not **text**)
- Use _text_ for italic
- Use `text` for inline code
- Use • or - for bullet points (not *)

Context: {context}
Question: {question}
Answer: """

            rag_prompt = PromptTemplate(
                template=rag_template, input_variables=["context", "question"]
            )

            # Create RAG chain
            self.rag_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vectorstore.as_retriever(
                    search_type="similarity", search_kwargs={"k": Config.RETRIEVAL_K}
                ),
                return_source_documents=True,
                chain_type_kwargs={"prompt": rag_prompt},
            )

            # General conversation prompt
            general_template = """
You are a friendly AI assistant. Respond naturally and conversationally.
Be helpful, engaging, and personable.

For Slack formatting:
- Use *text* for bold (not **text**)  
- Use _text_ for italic
- Use • or - for bullet points (not *)

User: {question}
Assistant: """

            self.general_prompt = PromptTemplate(
                template=general_template, input_variables=["question"]
            )

            self.is_ready = True
            logger.info("✅ RAG chatbot initialized successfully")

        except Exception as e:
            logger.error(f"Error setting up chains: {e}")
            self.is_ready = False

    def classify_query(self, question: str) -> str:
        """Classify query as 'rag', 'general', or 'mixed'"""
        question_lower = question.lower().strip()

        # Check continuation patterns
        is_continuation = any(
            re.search(pattern, question_lower, re.IGNORECASE)
            for pattern in self.continuation_patterns
        )

        if is_continuation and self.last_query_type:
            return self.last_query_type

        # Check general patterns
        is_general = any(
            re.search(pattern, question_lower, re.IGNORECASE)
            for pattern in self.general_patterns
        )

        if is_general:
            return "general"

        # Count document keywords
        doc_score = sum(
            1 for keyword in self.document_keywords if keyword in question_lower
        )

        if doc_score >= 2:
            return "rag"
        elif doc_score == 1:
            return "mixed"
        else:
            return "general"

    def add_to_history(self, question: str, answer: str, query_type: str):
        """Add conversation to history"""
        entry = {
            "timestamp": datetime.now(),
            "question": question,
            "answer": answer,
            "query_type": query_type,
        }

        self.conversation_history.append(entry)

        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history.pop(0)

    def get_conversation_context(self, current_question: str, limit: int) -> str:
        """Build context from recent conversation"""
        if not self.conversation_history:
            return ""

        recent_history = self.conversation_history[-limit:]
        context_parts = []

        for entry in recent_history:
            context_parts.append(f"Previous Q: {entry['question']}")
            context_parts.append(f"Previous A: {entry['answer']}")

        context = "\n".join(context_parts)
        return (
            f"Conversation context:\n{context}\n\nCurrent question: {current_question}"
        )

    def ask_rag(self, question: str) -> str:
        """Handle RAG queries"""
        try:
            # Build contextual query
            contextual_query = question
            if self.conversation_history:
                contextual_query = self.get_conversation_context(question, limit=2)

            result = self.rag_chain({"query": contextual_query})
            answer = result["result"].strip()

            if not answer:
                return (
                    "I don't find any relevant information in the available documents"
                )

            # Add source information
            source_docs = result.get("source_documents", [])
            if source_docs:
                sources = set()
                for doc in source_docs:
                    doc_name = doc.metadata.get("document_name", "Unknown")
                    sources.add(doc_name)

                if sources:
                    answer += f'\n\n_Sources: {", ".join(sources)}_'

            return answer

        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            return f"Sorry, I encountered an error processing your question: {str(e)}"

    def ask_general(self, question: str) -> str:
        """Handle general conversation"""
        try:
            # Build contextual prompt
            if self.conversation_history:
                context = self.get_conversation_context(question, limit=2)
                formatted_prompt = self.general_prompt.format(question=context)
            else:
                formatted_prompt = self.general_prompt.format(question=question)

            response = self.llm(formatted_prompt)

            return response.strip()

        except Exception as e:
            logger.error(f"Error in general query: {e}")
            return f"Sorry, I encountered an error: {str(e)}"

    def ask_mixed(self, question: str) -> str:
        """Handle mixed queries"""
        try:
            # Try RAG first
            rag_result = self.ask_rag(question)

            # If RAG found relevant information, use it
            if "don't find any relevant information" not in rag_result.lower():
                return rag_result

            # Otherwise, provide general response with suggestion
            general_response = self.ask_general(question)
            suggestion = f"\n\n💡 _If you're looking for specific information, try asking about: {', '.join(self.loaded_documents)}_"

            return general_response + suggestion

        except Exception as e:
            logger.error(f"Error in mixed query: {e}")
            return f"Sorry, I encountered an error: {str(e)}"

    def ask(self, question: str) -> str:
        """Main method - intelligently route questions"""
        if not self.is_ready:
            return "❌ System not ready"

        if not question.strip():
            return "Please ask me something! I can help with documents or just chat."

        # Classify and route query
        query_type = self.classify_query(question)

        if query_type == "rag":
            answer = self.ask_rag(question)
        elif query_type == "general":
            answer = self.ask_general(question)
        else:  # mixed
            answer = self.ask_mixed(question)

        # Store in history
        self.add_to_history(question, answer, query_type)
        self.last_query_type = query_type

        return answer

    def get_status(self) -> Dict:
        """Get system status"""
        return {
            "ready": self.is_ready,
            "documents": self.loaded_documents,
            "document_count": len(self.loaded_documents),
            "conversation_history_length": len(self.conversation_history),
            "capabilities": ["Natural conversation", "Document Q&A", "Smart routing"],
        }
