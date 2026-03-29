# STEER

**Safety Talent Entry and Education Router** — a Discord bot that helps newcomers find their path into AI safety.

## What it does

STEER conducts structured conversations to understand a user's background, skills, interests, and constraints, then provides tailored recommendations — pointing them to specific research agendas, papers, researchers, organisations, programs, and communities that match their profile.

It draws on the [Shallow Review of Technical AI Safety 2025](https://shallowreview.ai/overview) (~80 research agendas, 800+ papers) and broader ecosystem resources including governance, policy, and operations pathways.

## How to use it

- **`@STEER` in a channel** — creates a thread and starts a conversation
- **DM the bot** — chat directly in private messages
- **`/ask`** — slash command to start a conversation
- **`/roadmap`** — generates a personalised career roadmap as a downloadable markdown file (after enough conversation)
- **`/reset`** — clears conversation history and starts fresh

In threads, the bot auto-replies without needing to be mentioned again.

## Setup

### Prerequisites

- Python 3.12+
- A [Discord bot token](https://discord.com/developers/applications)
- A [Gemini API key](https://aistudio.google.com/apikey) (free)

### Install

```bash
git clone https://github.com/LouisP96/ai-safety-career-advisor-bot.git
cd ai-safety-career-advisor-bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
```

Edit `.env` with your keys:
```
DISCORD_TOKEN=your_discord_bot_token
GEMINI_API_KEY=your_gemini_api_key
```

### Discord bot setup

1. Create an application at [discord.com/developers/applications](https://discord.com/developers/applications)
2. Go to **Bot** > enable **Message Content Intent**
3. Go to **OAuth2** > **URL Generator** > select `bot` scope
4. Select permissions: Send Messages, Read Message History, View Channels
5. Use the generated URL to invite the bot to your server

### Run

```bash
python bot.py
```

## Deployment

Deployed on [Railway](https://railway.app). Pushing to `main` triggers auto-deploy.

Set `DISCORD_TOKEN` and `GEMINI_API_KEY` as service variables in Railway.

## Project structure

```
├── bot.py              # Discord bot logic
├── system_prompt.txt   # Advisor instructions and context
├── requirements.txt    # Python dependencies
├── Procfile            # Railway process definition
├── runtime.txt         # Python version for Railway
└── .env.example        # Template for environment variables
```

## Tech stack

- **[Pycord](https://docs.pycord.dev/)** — Discord bot framework
- **[Gemini 2.5 Flash](https://ai.google.dev/)** — LLM (free tier)
- **[INSPECT](https://inspect.ai-safety-institute.org.uk/)** — automated evaluation pipeline
- **[Railway](https://railway.app)** — deployment
