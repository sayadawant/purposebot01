import os
import discord
import openai
import time
import asyncio
import logging
import functools
from discord.ext import commands
from dotenv import load_dotenv
from prometheus_client import Counter, Summary, Gauge, generate_latest, CONTENT_TYPE_LATEST
from aiohttp import web

# ==========================
# Configuration and Setup
# ==========================

# Initialize logging to stdout and file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s',
    handlers=[
        logging.StreamHandler(),           # Logs to stdout
        logging.FileHandler("bot.log"),    # Logs to a file named bot.log
    ]
)

# Load environment variables from .env file
load_dotenv()

# Fetch environment variables
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT_TEXT")
MOAR_PROMPT = os.getenv("MOAR_PROMPT_TEXT")
PORT = int(os.getenv('PORT', 8000))  # Railway typically sets PORT

# Validate essential environment variables
if not DISCORD_BOT_TOKEN:
    logging.error("DISCORD_BOT_TOKEN environment variable not set.")
    exit(1)
if not OPENAI_API_KEY:
    logging.error("OPENAI_API_KEY environment variable not set.")
    exit(1)
if not SYSTEM_PROMPT:
    logging.error("SYSTEM_PROMPT_TEXT environment variable not set.")
    exit(1)
if not MOAR_PROMPT:
    logging.error("MOAR_PROMPT environment variable not set.")
    exit(1)

openai.api_key = OPENAI_API_KEY

# ==========================
# Prometheus Metrics Setup
# ==========================

REQUEST_LATENCY = Summary('response_latency_seconds', 'Response latency of the bot')
UPTIME_MINUTES = Gauge('bot_uptime_minutes', 'Bot uptime in minutes')
USER_INTERACTIONS = Counter('user_interactions_total', 'Total number of user interactions')
OPENAI_API_ERRORS = Counter('openai_api_errors_total', 'Total number of OpenAI API errors')
COMMAND_ERRORS = Counter('command_errors_total', 'Total number of command execution errors')
GENERAL_EXCEPTIONS = Counter('general_exceptions_total', 'Total number of unexpected exceptions')

# ==========================
# Discord Bot Setup
# ==========================

intents = discord.Intents.default()
intents.message_content = True

start_time = time.time()

bot = commands.Bot(command_prefix="!", intents=intents)

# ==========================
# Custom Decorator for Metrics
# ==========================

def prometheus_latency_metric(metric):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time_func = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                elapsed_time_func = time.time() - start_time_func
                metric.observe(elapsed_time_func)
        return wrapper
    return decorator

# ==========================
# Command Definitions
# ==========================

@bot.command()
@prometheus_latency_metric(REQUEST_LATENCY)
async def add(ctx, a: int, b: int):
    """Adds two numbers and returns the result, tracking metrics."""
    USER_INTERACTIONS.inc()
    result = a + b
    logging.info(f'Add command used by {ctx.author}: {a} + {b} = {result}')
    await ctx.send(f'The sum of {a} and {b} is {result}.')

@bot.command()
@prometheus_latency_metric(REQUEST_LATENCY)
async def purpose(ctx, *, user_message: str = ""):
    """Handles the purpose command by interacting with OpenAI."""
    if not user_message:
        await ctx.send("Please provide a question or statement, for example: `!purpose I'm worried about my future in a world where there is AGI.`")
        return
    
    try:
        completion = openai.chat.completions.create(
            model="gpt-4",  # Corrected model name
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            max_tokens=700,
            temperature=0.8,
            top_p=1.0,
            presence_penalty=0.2,
            frequency_penalty=0.1
        )

        bot_response = completion.choices[0].message.content.strip()
        USER_INTERACTIONS.inc()
        logging.info(f'Purpose command used by {ctx.author}: {user_message} -> {bot_response}')
        await ctx.send(bot_response)

    except openai.error.OpenAIError as e:
        OPENAI_API_ERRORS.inc()
        logging.exception(f"OpenAI API error: {e}")
        await ctx.send("Sorry, I encountered an issue while processing your request.")
    
    except Exception as e:
        GENERAL_EXCEPTIONS.inc()
        logging.exception(f"Unexpected error: {e}")
        await ctx.send("An unexpected error occurred. Please try again later.")

@bot.command()
@prometheus_latency_metric(REQUEST_LATENCY)
async def moar(ctx, *, user_message: str = ""):
    """Defines !moar command setting financial goals, tracking metrics."""
    if not user_message:
        await ctx.send("Please provide additional context or questions, for example: `!moar Please help me set financial targets for post-AGI future`")
        return
    
    try:
        completion = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": MOAR_PROMPT},
                {"role": "user", "content": user_message}
            ],
           max_tokens=700,
            temperature=0.8,
            top_p=1.0,
            presence_penalty=0.2,
            frequency_penalty=0.1
        )

        bot_response = completion.choices[0].message.content.strip()
        USER_INTERACTIONS.inc()
        logging.info(f'Moar command used by {ctx.author}: {user_message} -> {bot_response}')
        await ctx.send(bot_response)

    except openai.error.OpenAIError as e:
        OPENAI_API_ERRORS.inc()
        MOAR_COMMAND_ERRORS.inc()
        logging.exception(f"OpenAI API error in !moar command: {e}")
        await ctx.send("Sorry, I encountered an issue while processing your request with the !moar command.")

    except Exception as e:
        GENERAL_EXCEPTIONS.inc()
        MOAR_COMMAND_ERRORS.inc()
        logging.exception(f"Unexpected error in !moar command: {e}")
        await ctx.send("An unexpected error occurred while executing the !moar command. Please try again later.")

# ==========================
# Event Handlers
# ==========================

@bot.event
async def on_ready():
    logging.info(f'✅ Logged in as: {bot.user} (ID: {bot.user.id})')
    logging.info('------')
    # Start background task to update uptime
    bot.loop.create_task(update_uptime())

@bot.event
async def on_command_error(ctx, error):
    GENERAL_EXCEPTIONS.inc()
    logging.exception(f"Unhandled command error: {error}")
    await ctx.send("An error occurred while processing the command.")


# ==========================
# Uptime Tracking
# ==========================

async def update_uptime():
    """Background task to set uptime metric every minute."""
    while True:
        elapsed_time = time.time() - start_time
        uptime_minutes = elapsed_time / 60  # 
        UPTIME_MINUTES.set(uptime_minutes)
        await asyncio.sleep(60)

# ==========================
# Prometheus Metrics Endpoint
# ==========================

async def metrics_handler(request):
    """Handles the /metrics endpoint for Prometheus scraping."""
    try:
        logging.info(f"Received request for /metrics from {request.remote}")
        data = generate_latest()
        logging.info("Successfully generated metrics data.")
        return web.Response(body=data, content_type='text/plain; version=0.0.4')
    except Exception as e:
        logging.exception(f"Error generating metrics: {e}")
        return web.Response(status=500, text="Internal Server Error")

async def init_app():
    """Initializes the aiohttp web application."""
    app = web.Application()
    app.router.add_get('/metrics', metrics_handler)
    return app

# ==========================
# Bot and Server Runner
# ==========================

async def run_bot_and_server():
    """Runs both the Discord bot and the aiohttp server concurrently."""
    # Initialize aiohttp app
    app = await init_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    logging.info(f'Prometheus metrics available at /metrics on port {PORT}')

    try:
        await bot.start(DISCORD_BOT_TOKEN)
    except Exception as e:
        logging.exception(f"Bot encountered an error: {e}")
    finally:
        await runner.cleanup()

# ==========================
# Entry Point
# ==========================

if __name__ == '__main__':
    try:
        asyncio.run(run_bot_and_server())
    except KeyboardInterrupt:
        logging.info("Bot is shutting down.")
    except Exception as e:
        logging.exception("An error occurred: %s", e)
