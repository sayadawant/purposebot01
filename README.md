Purpose Agent Bot is an AI-assisted bot that leverages OpenAI to offer concise, empathetic coaching responses for users exploring their life purpose in a rapidly changing world. It listens for the !purpose command, sends a structured query to OpenAI (e.g., GPT-4o), and returns a tailored coaching message within a Discord server channel.

To configure the bot, place your Discord Bot Token, OpenAI API Key, and any custom system prompt text in a .env file. An example layout can be found in env.example, which outlines the variables needed to run the bot without exposing sensitive credentials in source control. The bot uses python-dotenv to load these variables at runtime.

Dependencies like discord.py and openai are listed in requirements.txt. You can install them via pip install -r requirements.txt, preferably inside a dedicated Python virtual environment. After installing, you can run python bot.py (with .env in place) to start the bot on your local machine.

Before testing or using the bot in production, invite the bot to a Discord server where you have sufficient permissions. Go to the Discord Developer Portal, generate an OAuth2 URL under “bot” scope (select the permissions you want), and paste that invite link in your browser to add the bot to your server.

Once running, the bot listens for the !purpose command and passes any user queries to OpenAI. It then responds with AI-generated guidance or insight, shaped by your system prompt and model parameters.