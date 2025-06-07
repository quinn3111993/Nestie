# Nestie
A RAG chatbot embedded in Slack, enabling Q&A on internal documents, Slack channel summarization and analysis, and normal chitchat like a companion at work.

## Features

- RAG-powered chatbot: Leverages document retrieval for contextually relevant responses
- Slack integration: Seamless interaction through Slack workspace
- Slack channel support: Summarize and analyze Slack channels

## Project Structure
```
├── documents           # Folder containing files to use for RAG
├── README.md           # Project documentation
├── config.py           # Configuration settings and environment variables
├── document_processor  # Document processing
├── main.py             # Main application entry point
├── rag_chatbot.py      # Core RAG chatbot implementation
├── requirements.txt    # Python dependencies
├── slack_bot.py        # Slack bot initialization and setup
└── slack_handlers.py   # Slack event handlers and message processing
```

## Prerequisites
- Python 3.8 or higher
- Slack workspace with admin access / available admin approval
- Gemini API Key (or other LLM provider)

## Installation
#### 1. Clone the repository
```
git clone https://github.com/quinn3111993/Nestie.git
cd Nestie
```

#### 2. Create virtual environment
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install dependencies
```
pip install -r requirements.txt
```

#### 4. Documents setup
Add your documents as inputs for RAG to folder `documents`


#### 5. Configuration setup

Edit the config.py file with your API keys and settings:
```
# API Keys
GOOGLE_API_KEY = "your-gemini-api-key"
SLACK_BOT_TOKEN = "xoxb-your-bot-token"
SLACK_APP_TOKEN = "xapp-your-app-token"

# Document paths
DOCUMENT_PATHS = {
"your-document1-name": "documents/your-document1.pdf",
"your-document2-name": "documents/your-document2.pdf",
...
}
```



## Slack App Setup

#### 1. Create Slack App
- Go to Slack API (https://api.slack.com/apps)
- Click "Create New App" → "From scratch"
- Name your app and select your workspace


#### 2. Configure Bot Permissions
Navigate to "OAuth & Permissions" and add these scopes:
- `app_mentions:read`
- `channels:history`
- `chat:write`
- `im:history`
- `im:read`
- `im:write`

#### 3. Enable Events
- Go to "Event Subscriptions"
- Enable events and set Request URL to your server endpoint
- Subscribe to bot events:
  - `app_mention`
  - `message.im`

#### 4. Install App
- Go to "Install App" and install to your workspace
- Go to "Basic Information" and copy the "App-Level Token" to put as `SLACK_APP_TOKEN` in config.py
- Go to "OAuth & Permissions" and copy the "Bot User OAuth Token" to put as `SLACK_BOT_TOKEN` in config.py


## Usage
#### Start the application
```
python main.py
```

#### Interact with the bot

<div align="center">
<img width="600" alt="Screenshot 2025-06-06 at 22 48 54" src="https://github.com/user-attachments/assets/ae0d0943-c42c-4332-9c39-5e3d073d74f0" />
  <br>
  <em>Direct message the bot in Slack</em>
</div>
<br>
<br>

<div align="center">
<img width="600" alt="RAG" src="https://github.com/user-attachments/assets/a759b15b-f94d-4ccf-bfb1-e5943ac84909" />
  <br>
  <em>The bot will use RAG to provide contextually relevant responses</em>
</div>
<br>
<br>

<div align="center">
<img width="600" alt="channel summary" src="https://github.com/user-attachments/assets/94fe5657-c9f7-47ac-9e7c-b13a014f1f28" />
  <br>
  <em>And access Slack channels to provide analysis or summarization requests</em>
</div>
<br>

## Future Development

Module Overview
- `main.py`: Application entry point, initializes and coordinates all components
- `config.py`: Centralized configuration management
- `document_processor.py`: Document processing module for loading, chunking, and vectorizing documents
- `rag_chatbot.py`: Core chatbot logic, document retrieval, and response generation
- `slack_bot.py`: Slack bot initialization and connection management
- `slack_handlers.py`: Event handling, message processing, and Slack API interactions

Adding Features
- New/adjusting document processing: Update `document_processor.py`
- New RAG capabilities: Extend `rag_chatbot.py`
- Additional Slack features: Add handlers in `slack_handlers.py`
- Configuration options: Update `config.py`
- New integrations: Create new modules and import in `main.py`
