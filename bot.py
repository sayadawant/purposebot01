import os
import discord
import openai
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")
system_prompt = os.getenv("SYSTEM_PROMPT_TEXT")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as: {bot.user} (ID: {bot.user.id})")

@bot.command()
async def purpose(ctx, *, user_message: str = ""):
    if not user_message:
        await ctx.send("Please provide a question or statement, for example: `!purpose I'm worried about my future in a world where there is AGI.`")
        return
    
    try:

        completion = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=350,
            temperature=0.8,
            top_p=1.0,
            presence_penalty=0.2,
            frequency_penalty=0.1
        )

        bot_response = completion.choices[0].message.content
        await ctx.send(bot_response)

    except Exception as e:
        print(f"OpenAI error: {e}")
        await ctx.send("Sorry, I had trouble generating a response. Please try again later.")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
