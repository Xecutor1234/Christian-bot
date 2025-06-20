import discord
import os
from keep_alive import keep_alive
import requests
# No longer need PIL or io, so they have been removed.
from google.generativeai.generative_models import GenerativeModel

# We rely on the automatic key detection of GOOGLE_API_KEY

# Define the intents your bot needs
intents = discord.Intents.default()
intents.message_content = True

# Create a client instance
client = discord.Client(intents=intents)

# --- HELPER FUNCTION FOR AI CHAT ---
async def get_gemini_chat_response(user_message):
    try:
        model = GenerativeModel('gemini-1.5-flash-latest')

        chat_session = model.start_chat(history=[
            {"role": "user", "parts": ["SYSTEM_INSTRUCTION"]},
            {"role": "model", "parts": ["You are a kind, knowledgeable, and compassionate Christian AI assistant. Your purpose is to help users by answering questions about the Bible, Christian faith, and theology. Provide encouragement and support grounded in Christian principles. When citing scripture, please provide the reference (e.g., John 3:16). Always maintain a respectful and loving tone. You are a helpful guide, not a replacement for a pastor or personal study."]}
        ])

        response = chat_session.send_message(user_message)
        return response.text

    except Exception as e:
        print(f"Gemini Chat API Error: {e}")
        return "I'm sorry, I'm having a little trouble connecting to my thoughts right now. Please try again in a moment."

# Event: When the bot is ready and online
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

# The main message-handling event
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    is_server_channel = isinstance(message.channel, discord.TextChannel)
    is_dm_channel = isinstance(message.channel, discord.DMChannel)

    # --- FEATURE 1: AI IMAGE GENERATION (NEW, WORKING METHOD) ---
    if is_server_channel and message.channel.name == 'christian-ai-image-generation🎨':
        async with message.channel.typing():
            prompt = message.content
            # We add extra descriptive words to get better images
            full_prompt = f"A high-quality, inspiring, respectful, cinematic image of: {prompt}"

            # The URL for the Pollinations.ai image generation service
            image_url = f"https://image.pollinations.ai/prompt/{full_prompt}"

            await message.channel.send(f"Generating an image for: \"{prompt}\"...")

            try:
                # We simply send the URL, and Discord will automatically show the image
                await message.channel.send(image_url)

            except Exception as e:
                print(f"Image Generation Error: {e}")
                await message.channel.send("Sorry, I was unable to generate an image for that prompt. Please try a different one.")
        return

    # --- FEATURE 2: AI CHATBOT IN DMs and a specific channel ---
    if (is_server_channel and message.channel.name == 'chat-with-christian-bot') or is_dm_channel:
        if message.content.startswith('!'):
            return

        async with message.channel.typing():
            response_text = await get_gemini_chat_response(message.content)
            await message.channel.send(response_text)
        return

    # --- YOUR OTHER COMMANDS ---
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