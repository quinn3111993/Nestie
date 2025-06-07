# -*- coding: utf-8 -*-
"""
Slack Handlers
Contains all Slack event handlers and message processing logic for the RAG bot.
"""

import os
import logging
from slack_bolt import App
from config import Config

# Setup logging
logger = logging.getLogger(__name__)


def create_slack_app():
    """
    Create and configure the Slack app

    Returns:
        App: Configured Slack Bolt app instance
    """
    try:
        # Set environment variables
        os.environ["SLACK_BOT_TOKEN"] = Config.SLACK_BOT_TOKEN
        os.environ["SLACK_APP_TOKEN"] = Config.SLACK_APP_TOKEN

        # Initialize Slack app
        app = App(token=Config.SLACK_BOT_TOKEN)

        logger.info("✅ Slack app configured successfully")
        return app

    except Exception as e:
        logger.error(f"❌ Error creating Slack app: {e}")
        raise


def register_handlers(app, slack_bot):
    """
    Register all Slack event handlers

    Args:
        app: Slack Bolt app instance
        slack_bot: SlackRAGBot instance
    """

    @app.message("hello")
    def handle_hello(message, say):
        """Handle hello messages"""
        try:
            user = message["user"]
            say(
                f"Hello <@{user}> :wave:! I'm Nestie - your assistant and companion at work. Ask me anything about our company!"
            )
            logger.info(f"Handled hello message from user {user}")
        except Exception as e:
            logger.error(f"Error handling hello message: {e}")
            say("Hello! I'm having some trouble right now, but I'm here to help!")

    @app.message("help")
    def handle_help(message, say):
        """Handle help messages"""
        try:
            help_text = """
🤖 *Document Assistant Help*

I can answer questions about the company internal documents and channels, and talk with you as a friend too. Here are some examples:

• "Tell me about our company policies"
• "What are the core values in our company culture?"
• "Summarize #channel-name today"

📝 *Available Commands:*
• `hello` - Say hi
• `help` - Show this help
• `status` - Check system status
• `summarize #channel-name` - Get a summary of recent content
• `what's happening in #channel-name today?` - Recent activity overview
• Just ask any question naturally!

⌛ *Time Filters for asking about channels:*
• today, yesterday, last week, last month

💡 *Tips:*
• Be specific in your questions
• I'll show you which documents I found the information in
• If I can't find something, try rephrasing your question
            """

            say(help_text)
            logger.info(f"Provided help to user {message['user']}")

        except Exception as e:
            logger.error(f"Error handling help message: {e}")
            say(
                "I'm having trouble accessing the help information right now. Please try again later!"
            )

    @app.message("status")
    def handle_status(message, say):
        """Handle status messages"""
        try:
            if slack_bot and slack_bot.is_ready:
                status = slack_bot.rag_chatbot.get_status()
                status_text = f"""
📊 *System Status*

✅ Status: Ready
📚 Documents loaded: {status['document_count']}
📄 Available documents: {', '.join(status['loaded_documents'])}

Ready to answer your questions!
"""
                logger.info(f"Provided status to user {message['user']} - System Ready")
            else:
                status_text = """
📊 *System Status*

❌ Status: Not Ready
The document system is currently unavailable. Please contact an admin.
"""
                logger.warning(
                    f"Status check from user {message['user']} - System Not Ready"
                )

            say(status_text)

        except Exception as e:
            logger.error(f"Error handling status message: {e}")
            say(
                "I'm having trouble checking the system status right now. Please try again later!"
            )

    @app.event("app_mention")
    def handle_mention(event, say):
        """Handle app mention events"""
        try:
            text = event["text"]
            user = event["user"]

            # Remove the mention from the text
            mention_text = text.split(">", 1)[-1].strip()

            logger.info(f"App mentioned by user {user}: {mention_text}")

            if mention_text:
                if slack_bot and slack_bot.is_ready:
                    answer = slack_bot.get_answer(mention_text, user)
                    say(f"<@{user}> {answer}")
                    logger.info(f"Responded to mention from user {user}")
                else:
                    say(
                        f"<@{user}> Sorry, the document system is not ready yet. Please contact the admin."
                    )
                    logger.warning(
                        f"Could not respond to mention from user {user} - system not ready"
                    )
            else:
                say(f"<@{user}> 👋 Hi, you can ask me any question!")
                logger.info(f"Greeted user {user} after mention")

        except Exception as e:
            logger.error(f"Error handling app mention: {e}")
            try:
                say(
                    f"<@{event['user']}> Sorry, I encountered an error. Please try again!"
                )
            except:
                pass

    @app.message("")
    def handle_direct_message(message, say):
        """
        Handle direct messages (main functionality)
        This is where questions get processed by the RAG system
        """
        try:
            user = message["user"]
            text = message["text"].strip()

            # Skip if it's a command we already handle
            if text.lower() in ["hello", "help", "status"]:
                return

            # Skip empty messages
            if not text:
                say("🤔 Please ask me a specific question!")
                return

            logger.info(f"Processing question from user {user}: {text[:100]}...")

            # Get answer from RAG system
            if slack_bot and slack_bot.is_ready:
                # Optionally show thinking indicator for complex queries
                # say('⏳ Let me think...')

                answer = slack_bot.get_answer(text, user)
                say(f"<@{user}> {answer}")
                logger.info(f"Successfully responded to user {user}")
            else:
                say(
                    "🚫 Sorry, the document system is not ready yet. Please contact the admin."
                )
                logger.warning(f"Could not respond to user {user} - system not ready")

        except Exception as e:
            logger.error(f"Error processing message from user {user}: {e}")
            try:
                say(
                    f"<@{user}> 😅 Sorry, I encountered an error. Please try again or contact support."
                )
            except:
                pass

    @app.error
    def global_error_handler(error, body, logger):
        """Global error handler for unhandled exceptions"""
        logger.error(f"Global error: {error}")
        logger.error(f"Request body: {body}")

    # Register additional event handlers if needed
    @app.event("message")
    def handle_message_events(event, logger):
        """Handle message events that don't match other patterns"""
        # This can be used for logging or additional processing
        # Currently just logs the event for debugging
        if event.get("subtype") is None:  # Only log regular messages
            logger.debug(f"Message event: {event.get('text', '')[:50]}...")

    @app.event("team_join")
    def handle_team_join(event, say, logger):
        """Welcome new team members"""
        try:
            user_id = event["user"]["id"]
            welcome_message = f"""
👋 Welcome to the team, <@{user_id}>!

I'm Nestie, your AI assistant! I can help you with:
• Company policies and procedures
• Document summaries
• Channel activity summaries
• General conversation

Type `help` to see what I can do, or just ask me anything!
"""
            # Send welcome message to general channel or DM
            # You might want to customize this based on your needs
            logger.info(f"New team member joined: {user_id}")

        except Exception as e:
            logger.error(f"Error handling team join event: {e}")

    @app.command("/nestie")
    def handle_slash_command(ack, respond, command):
        """Handle slash commands"""
        try:
            ack()  # Acknowledge the command

            user_id = command["user_id"]
            text = command["text"].strip()

            logger.info(f"Slash command from user {user_id}: {text}")

            if not text:
                respond(
                    "Hi! You can ask me questions using the slash command. For example: `/nestie what are our working hours?`"
                )
                return

            if slack_bot and slack_bot.is_ready:
                answer = slack_bot.get_answer(text, user_id)
                respond(f"{answer}")
            else:
                respond(
                    "Sorry, the document system is not ready yet. Please contact the admin."
                )

        except Exception as e:
            logger.error(f"Error handling slash command: {e}")
            try:
                respond(
                    "Sorry, I encountered an error processing your command. Please try again!"
                )
            except:
                pass

    @app.event("reaction_added")
    def handle_reaction_added(event, logger):
        """Handle reaction events for analytics"""
        try:
            # This can be used for feedback collection or analytics
            logger.debug(
                f"Reaction added: {event.get('reaction')} by {event.get('user')}"
            )
        except Exception as e:
            logger.error(f"Error handling reaction: {e}")

    logger.info("✅ All Slack handlers registered successfully")


def create_help_text():
    """
    Create formatted help text for the bot

    Returns:
        str: Formatted help text
    """
    return """
🤖 *Nestie - Your AI Assistant*

*What I can do:*
• Answer questions about company documents
• Summarize Slack channel activity
• Have natural conversations
• Provide company policy information

*Commands:*
• `hello` - Greet me
• `help` - Show this help
• `status` - Check system status

*Examples:*
• "What's our hybrid working policy?"
• "Summarize #dev-team today"
• "What happened in #general yesterday?"

*Channel Analysis:*
Use time filters like: today, yesterday, last week, last month

*Tips:*
• Be specific in your questions
• I'll show you source documents
• Tag me with @nestie for mentions
"""


def format_error_message(error_type="general"):
    """
    Format error messages consistently

    Args:
        error_type (str): Type of error for customized messages

    Returns:
        str: Formatted error message
    """
    error_messages = {
        "general": "😅 Sorry, I encountered an error. Please try again or contact support.",
        "system_not_ready": "🚫 Sorry, the document system is not ready yet. Please contact an admin.",
        "empty_query": "🤔 Please ask me a specific question!",
        "channel_access": "🔒 I don't have access to that channel or couldn't find recent messages.",
        "processing": "⚠️ I'm having trouble processing your request. Please try rephrasing your question.",
    }

    return error_messages.get(error_type, error_messages["general"])
