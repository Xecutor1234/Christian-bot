import discord
import os
import requests
from keep_alive import keep_alive
# --- THIS IS THE FINAL, PRECISE FIX ---
# The error message told us the exact import path to use.
from google.generativeai.generative_models import GenerativeModel
# ------------------------------------

# We rely on the automatic key detection of GOOGLE_API_KEY

# Define the intents your bot needs
intents = discord.Intents.default()
intents.message_content = True

# Create a client instance
client = discord.Client(intents=intents)

# Event: When the bot is ready and online
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

# The main message-handling event
@client.event
async def on_message(message):
    # Don't let the bot respond to its own messages
    if message.author == client.user:
        return

    # Check if the message is in a server channel to avoid DM crashes
    is_server_channel = isinstance(message.channel, discord.TextChannel)

    # AI Chatbot Logic
    if is_server_channel and message.channel.name == 'chat-with-christian-bot':
        if message.content.startswith('!'):
            return

        async with message.channel.typing():
            try:
                # We still don't need "genai." before this because we imported it directly
                model = GenerativeModel(
                    'gemini-1.5-flash-latest',
                    system_instruction="You are a kind, knowledgeable, and compassionate Christian AI assistant. Your purpose is to help users by answering questions about the Bible, Christian faith, and theology. Provide encouragement and support grounded in Christian principles. When citing scripture, please provide the reference (e.g., John 3:16). Always maintain a respectful and loving tone. You are a helpful guide, not a replacement for a pastor or personal study."
                )

                chat_session = model.start_chat()
                response = chat_session.send_message(message.content)
                await message.channel.send(response.text)

            except Exception as e:
                print(f"Gemini API Error: {e}")
                await message.channel.send("I'm sorry, I'm having a little trouble connecting to my thoughts right now. Please try again in a moment.")
        return

    # Regular Commands
    if message.content.startswith('!ping'):
        await message.channel.send('Pong!')

    if message.content.startswith('!dailyverse'):
        try:
            api_url = "https://bible-api.com/?random=verse"
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()
            reference = data['reference']
            verse_text = data['text'].replace('\n', ' ').strip()
            formatted_message = f"**{reference}**\n> {verse_text}"
            await message.channel.send(formatted_message)
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            await message.channel.send("Sorry, I couldn't fetch a verse right now. Please try again later.")

# Keep Alive and Bot Run Logic
keep_alive()

token = os.getenv('DISCORD_TOKEN')
if token is None:
    print("=" * 50)
    print("CRITICAL ERROR: The DISCORD_TOKEN secret was not found.")
    print("Please go to the 'Secrets' tab and add your key.")
    print("=" * 50)
else:
    client.run(token)