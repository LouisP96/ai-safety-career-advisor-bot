import discord
import io
import os
from google import genai
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Bot(intents=intents)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Load system prompt
prompt_path = Path(__file__).parent / "system_prompt.txt"
system_prompt = prompt_path.read_text()

# Conversation history keyed by thread ID (one conversation per thread)
conversations = {}

# Track which threads the bot created so it knows to auto-reply in them
active_threads = set()

MAX_HISTORY = 20  # keep last 10 exchanges (20 messages)
MODEL = "gemini-2.5-pro"
MAX_TOKENS = 1500


async def get_response(thread_id: int, message_content: str) -> str:
    if thread_id not in conversations:
        conversations[thread_id] = []

    conversations[thread_id].append({"role": "user", "content": message_content})
    conversations[thread_id] = conversations[thread_id][-MAX_HISTORY:]

    # Build contents for Gemini format
    contents = []
    for msg in conversations[thread_id]:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    response = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config={
            "system_instruction": system_prompt,
            "max_output_tokens": MAX_TOKENS,
        },
    )

    reply = response.text
    conversations[thread_id].append({"role": "assistant", "content": reply})
    return reply


async def send_reply(channel, reply: str):
    """Send a reply, splitting into chunks if over Discord's 2000 char limit."""
    chunks = []
    while len(reply) > 1900:
        split_at = reply.rfind("\n", 0, 1900)
        if split_at == -1:
            split_at = 1900
        chunks.append(reply[:split_at])
        reply = reply[split_at:].lstrip("\n")
    chunks.append(reply)

    for chunk in chunks:
        await channel.send(chunk)


async def create_thread_and_reply(message):
    """Create a thread from the message, then reply in it."""
    content = message.content.replace(f"<@{bot.user.id}>", "").strip()
    if not content:
        content = "Hi, I'm interested in AI safety."

    # Create a thread from the user's message
    thread = await message.create_thread(
        name=f"AI Safety Career Chat",
        auto_archive_duration=60,
    )
    active_threads.add(thread.id)

    async with thread.typing():
        reply = await get_response(thread.id, content)
    await send_reply(thread, reply)


@bot.slash_command(description="Ask about getting into AI safety")
async def ask(ctx, question: str):
    await ctx.defer()

    # Send initial response in channel, then create thread
    response_msg = await ctx.respond(f"Starting a conversation about: *{question[:100]}*...")
    original_message = await ctx.interaction.original_response()

    thread = await original_message.create_thread(
        name="AI Safety Career Chat",
        auto_archive_duration=60,
    )
    active_threads.add(thread.id)

    async with thread.typing():
        reply = await get_response(thread.id, question)
    await send_reply(thread, reply)


ROADMAP_PROMPT = """Based on the conversation so far, generate a personalised AI Safety Career Roadmap for this user as a clean markdown document. Include:

## About You
A brief summary of their background, skills, and interests as you understand them.

## Recommended Research Areas
The 1-3 research agendas that best fit them, with a sentence on why each is a good fit.

## Reading List
3-5 specific papers or posts to start with (only ones mentioned in the Shallow Review context), with URLs where available.

## Key People & Organisations
Researchers and orgs to follow, relevant to their recommended areas.

## Suggested First Steps
2-3 concrete actions they can take in the next 1-3 months (e.g. read X, apply to Y programme, build Z).

## Honest Assessment
Brief note on competitiveness, gaps to fill, and realistic timeline.

Format it as clean markdown. Be specific, not generic."""


@bot.slash_command(description="Generate your personalised AI safety career roadmap")
async def roadmap(ctx):
    thread_id = ctx.channel.id
    if thread_id not in conversations or len(conversations[thread_id]) < 4:
        await ctx.respond(
            "I need a bit more conversation first to give you a good roadmap. "
            "Tell me more about your background and interests, then try `/roadmap` again."
        )
        return

    await ctx.defer()

    contents = []
    for msg in conversations[thread_id]:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    contents.append({"role": "user", "parts": [{"text": ROADMAP_PROMPT}]})

    response = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config={
            "system_instruction": system_prompt,
            "max_output_tokens": 3000,
        },
    )

    roadmap_text = response.text
    file = discord.File(
        io.BytesIO(roadmap_text.encode("utf-8")),
        filename="ai-safety-career-roadmap.md",
    )
    await ctx.respond("Here's your personalised roadmap:", file=file)


@bot.slash_command(description="Reset the conversation in this thread")
async def reset(ctx):
    thread_id = ctx.channel.id
    conversations.pop(thread_id, None)
    await ctx.respond("Conversation reset. Ask me anything about getting into AI safety.")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # DMs — reply directly, no threads needed
    if isinstance(message.channel, discord.DMChannel):
        try:
            async with message.channel.typing():
                reply = await get_response(message.channel.id, message.content)
            await send_reply(message.channel, reply)
        except Exception as e:
            print(f"Error in DM reply: {e}")
            await message.channel.send(f"Sorry, something went wrong: {e}")
        return

    # If this message is in an active thread, auto-reply (no @ needed)
    if message.channel.id in active_threads:
        try:
            async with message.channel.typing():
                reply = await get_response(message.channel.id, message.content)
            await send_reply(message.channel, reply)
        except Exception as e:
            print(f"Error in thread reply: {e}")
            await message.channel.send(f"Sorry, something went wrong: {e}")
        return

    # If mentioned in a regular channel, create a thread
    if bot.user.mentioned_in(message):
        await create_thread_and_reply(message)
        return


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"System prompt length: {len(system_prompt)} chars")


bot.run(os.getenv("DISCORD_TOKEN"))
