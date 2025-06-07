"""
Slack bot integration module with channel analysis capabilities
"""

import os
import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from config import Config
from rag_chatbot import RAGChatbot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SlackRAGBot:
    """
    Slack Chatbot that integrates with the RAG system
    """

    def __init__(self, rag_chatbot, slack_client):
        self.rag_chatbot = rag_chatbot
        self.is_ready = rag_chatbot.is_ready if rag_chatbot else False
        self.slack_client = slack_client

    def get_answer(self, question: str, user_id: Optional[str] = None) -> str:
        """
        Get answer from RAG system with Slack-friendly formatting
        Handle both regular questions and channel-based commands
        """
        try:
            if not self.is_ready:
                return "🚫 Sorry, the document system is not ready yet. Please contact an admin."

            # Check if this is channel related command
            channel_command = self._parse_channel_command(question)
            if channel_command:
                logger.info("Processing channel command")
                return self._handle_channel_command(channel_command, user_id)

            # Regular question, get answer from RAG chatbot
            logger.info("Processing regular question")
            answer = self.rag_chatbot.ask(question)

            # Format for Slack
            if "Error:" in answer:
                return f"❌ {answer}"
            elif (
                "I don't find any relevant information in the available documents"
                in answer
            ):
                return f"🤔 Please try rephrasing your question so that I can understand you better."
            else:
                return f"{answer}"

        except Exception as e:
            logger.error(f"Error getting answer for user {user_id}: {e}")
            return (
                "😅 Sorry, I encountered an error. Please try again or contact support."
            )

    def _parse_channel_command(self, question: str) -> Optional[Dict[str, Any]]:
        """
        Parse channel-related commands
        """
        question_lower = question.lower().strip()

        # Extract mentioned channel
        channel_match = re.search(r"<#([a-zA-Z0-9]+)\|>", question_lower)
        logger.debug(f"Question: {question_lower}")
        logger.debug(f"Channel match: {channel_match}")

        if not channel_match:
            return None

        channel_id = channel_match.group(1).upper()

        # Define command type and time filter
        command_type = None
        time_filter = None

        if any(
            word in question_lower
            for word in [
                "analyze" "recent",
                "activity",
                "overview",
                "happen",
                "happening",
                "happened",
            ]
        ):
            command_type = "activity"
        else:
            command_type = "summarize"

        if "yesterday" in question_lower:
            time_filter = "yesterday"
        elif "week" in question_lower:
            time_filter = "week"
        elif "month" in question_lower:
            time_filter = "month"
        else:
            time_filter = "today"

        return {
            "channel_id": channel_id,
            "command_type": command_type,
            "time_filter": time_filter,
            "original_query": question,
        }

    def _handle_channel_command(
        self, command: Dict[str, Any], user_id: Optional[str]
    ) -> str:
        """
        Handle channel-related commands
        """
        try:
            channel_id = command["channel_id"]
            command_type = command["command_type"]
            time_filter = command["time_filter"]

            logger.info(f"Processing {command_type} for channel {channel_id}")

            # Get channel messages
            messages = self._get_channel_messages(channel_id, time_filter)
            if not messages:
                return f"I couldn't find any recent messages in that channel or I don't have access to it."

            # Process based on command type
            if command_type == "activity":
                return self._analyze_activity(channel_id, messages, time_filter)
            else:
                return self._summarize_channel(channel_id, messages, time_filter)

        except Exception as e:
            logger.error(f"Error handling channel command for user {user_id}: {e}")
            return "😅 Sorry, I encountered an error processing the channel command. Please try again or contact support."

    def _get_channel_messages(self, channel_id: str, time_filter: str) -> list:
        """
        Get messages from a channel
        """
        if not self.slack_client:
            raise Exception("Slack client not configured")

        try:
            if not channel_id:
                return []

            # Calculate time range
            now = datetime.now()
            if time_filter == "today":
                oldest = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_filter == "yesterday":
                oldest = now.replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) - timedelta(days=1)
            elif time_filter == "week":
                oldest = now - timedelta(days=7)
            elif time_filter == "month":
                oldest = now - timedelta(days=30)
            else:
                oldest = now - timedelta(hours=24)

            # Fetch messages
            response = self.slack_client.conversations_history(
                channel=channel_id, oldest=oldest.timestamp(), limit=200
            )

            messages = []
            for msg in response["messages"]:
                if "text" in msg and msg["text"].strip():
                    user_info = self._get_user_info(msg.get("user", "Unknown"))
                    messages.append(
                        {
                            "text": msg["text"],
                            "user": user_info,
                            "timestamp": datetime.fromtimestamp(float(msg["ts"])),
                            "reactions": msg.get("reactions", []),
                        }
                    )

            return sorted(messages, key=lambda x: x["timestamp"])

        except Exception as e:
            logger.error(f"Error getting channel messages from {channel_id}: {e}")
            return []

    def _get_user_info(self, user_id: str) -> str:
        """
        Get user information
        """
        try:
            if user_id == "Unknown":
                return "Unknown User"
            response = self.slack_client.users_info(user=user_id)
            return response["user"].get("display_name", "Unknown User")
        except:
            return "Unknown User"

    def _analyze_activity(
        self, channel_id: str, messages: list, time_filter: str
    ) -> str:
        """
        Analyze channel activity
        """
        if not messages:
            return f"📭 No activity found in the channel for {time_filter}."

        # Basic activity metrics
        total_messages = len(messages)
        unique_users = len(set(msg["user"] for msg in messages))
        most_active_user = max(
            set(msg["user"] for msg in messages),
            key=lambda u: sum(1 for m in messages if m["user"] == u),
        )

        # Time distribution
        hours = [msg["timestamp"].hour for msg in messages]
        peak_hour = max(set(hours), key=hours.count) if hours else 0

        activity_summary = f"""📈 *Activity Summary* ({time_filter}):

• *{total_messages}* total messages
• *{unique_users}* active participants
• Most active: *{most_active_user}*
• Peak activity: *{peak_hour}:00*

Recent highlights:"""

        # Add recent message highlights
        recent_messages = messages[-3:] if len(messages) >= 3 else messages
        for msg in recent_messages:
            activity_summary += f"\n• {msg['user']}: {msg['text'][:100]}{'...' if len(msg['text']) > 100 else ''}"

        return activity_summary

    def _summarize_channel(
        self, channel_id: str, messages: list, time_filter: str
    ) -> str:
        """
        Summarize channel messages
        """
        if not messages:
            return f"📭 No messages found in the channel for {time_filter}."

        # Prepare content for RAG system
        message_text = self._format_messages_for_analysis(messages)

        # Use RAG system to generate summary
        summary_prompt = f"""
        Please provide a concise summary of the following Slack channel conversation ({time_filter}):

        {message_text}

        Focus on:
        - Main topics discussed
        - Key decisions or announcements
        - Important questions or issues raised
        - Action items mentioned
        """

        summary = self.rag_chatbot.ask(summary_prompt)

        return f"📊 *Channel Summary* ({time_filter}):\n\n{summary}\n\n_Analyzed {len(messages)} messages_"

    def _format_messages_for_analysis(self, messages: list) -> str:
        """
        Format messages for analysis
        """
        formatted = []
        for msg in messages:
            timestamp = msg["timestamp"].strftime("%H:%M")
            formatted.append(f"[{timestamp}] {msg['user']}: {msg['text']}")

        # Limit content to avoid token limits
        full_text = "\n".join(formatted)
        if len(full_text) > 8000:
            # Take recent messages that fit within limit
            recent_text = ""
            for msg in reversed(formatted):
                if len(recent_text + msg) < 8000:
                    recent_text = msg + "\n" + recent_text
                else:
                    break
            return recent_text

        return full_text
