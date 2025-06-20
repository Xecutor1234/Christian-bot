import discord
import os
from keep_alive import keep_alive
import requests
from google.generativeai.generative_models import GenerativeModel
from urllib.parse import quote

# We rely on the automatic key detection of GOOGLE_API_KEY

# Define the intents your bot needs
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

# Create a client instance
client = discord.Client(intents=intents)

# --- PRAYER REQUEST MODAL ---
class PrayerRequestModal(discord.ui.Modal, title='Submit a Prayer Request'):
    request_text = discord.ui.TextInput(
        label='What can we pray for you about?',
        style=discord.TextStyle.paragraph,
        placeholder='Please share your request here. It will be sent privately to our prayer team.',
        required=True,
        max_length=1000,
    )

    # This code runs when the user clicks the "Submit" button
    async def on_submit(self, interaction: discord.Interaction):
        log_channel_id_str = os.getenv('PRAYER_LOG_CHANNEL_ID')

        if log_channel_id_str is None:
            print("CRITICAL ERROR: PRAYER_LOG_CHANNEL_ID secret is not set in the environment.")
            await interaction.response.send_message('Sorry, the prayer request system is not configured correctly. Please contact an admin.', ephemeral=True)
            return

        try:
            log_channel_id = int(log_channel_id_str)
            log_channel = client.get_channel(log_channel_id)

            author_icon_url = interaction.user.default_avatar.url
            if interaction.user.avatar:
                author_icon_url = interaction.user.avatar.url

            log_embed = discord.Embed(
                title="New Prayer Request",
                description=self.request_text.value,
                color=discord.Color.blue()
            )
            log_embed.set_author(name=f"From: {interaction.user.name}", icon_url=author_icon_url)
            log_embed.set_footer(text=f"User ID: {interaction.user.id}")

            # --- THIS IS THE FINAL FIX ---
            # Check if the channel was found AND if it is a TextChannel before sending.
            if log_channel and isinstance(log_channel, discord.TextChannel):
                await log_channel.send(embed=log_embed)
                await interaction.response.send_message('Thank you for your submission. Your prayer request has been received and will be lifted up in prayer. God bless you.', ephemeral=True)
            else:
                # This handles both cases: channel not found, or wrong channel type
                print(f"ERROR: Could not find a valid TEXT channel with ID {log_channel_id}. Please check the PRAYER_LOG_CHANNEL_ID secret.")
                await interaction.response.send_message('Sorry, the prayer request system has a configuration error. Please contact a server admin.', ephemeral=True)
            # ---------------------

        except ValueError:
            print(f"ERROR: PRAYER_LOG_CHANNEL_ID is not a valid integer. Value: {log_channel_id_str}")
            await interaction.response.send_message('Sorry, the prayer request system has a configuration error. Please contact an admin.', ephemeral=True)

# --- PRAYER REQUEST VIEW ---
class PrayerRequestView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Request Prayer', style=discord.ButtonStyle.primary, custom_id='prayer_request_button')
    async def prayer_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PrayerRequestModal())


# --- BOT EVENTS ---
@client.event
async def on_ready():
    client.add_view(PrayerRequestView())
    print(f'We have logged in as {client.user}')
    print('Prayer request button view has been registered.')


# --- The Main on_message function ---
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # SETUP COMMAND for the Prayer Request Button
    if message.content == '!sendprayer':
        if not message.author.guild_permissions.administrator:
            await message.channel.send("Sorry, only administrators can use this command.", delete_after=10)
            await message.delete()
            return
        if message.channel.name != 'prayer-requests🙏':
            await message.channel.send("This command can only be used in the #prayer-requests🙏 channel.", delete_after=10)
            await message.delete()
            return

        embed = discord.Embed(
            title="Prayer Requests",
            description="If you have a prayer request, please click the button below. Your submission will be completely private and sent only to our trusted prayer team.",
            color=discord.Color.gold()
        )
        await message.channel.send(embed=embed, view=PrayerRequestView())
        await message.delete()
        return

    # Check the type of channel for other features
    is_server_channel = isinstance(message.channel, discord.TextChannel)
    is_dm_channel = isinstance(message.channel, discord.DMChannel)

    # Image Generation Feature
    if is_server_channel and message.channel.name == 'christian-ai-image-generation🎨':
        async with message.channel.typing():
            prompt = message.content
            full_prompt = f"A high-quality, inspiring, respectful, cinematic image of: {prompt}"
            encoded_prompt = quote(full_prompt)
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"

            await message.channel.send(f"Generating an image for: \"{prompt}\"...")
            await message.channel.send(image_url)
        return

    # Chatbot Feature
    if (is_server_channel and message.channel.name == 'chat-with-christian-bot') or is_dm_channel:
        if message.content.startswith('!'):
            return
        async with message.channel.typing():
            response_text = await get_gemini_chat_response(message.content)
            await message.channel.send(response_text)
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
            await message.channel.send("Sorry, I couldn't fetch a verse right now.")
        return

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

# --- Keep Alive and Bot Run Logic ---
keep_alive()

token = os.getenv('DISCORD_TOKEN')
if token is None:
    print("=" * 50)
    print("CRITICAL ERROR: The DISCORD_TOKEN secret was not found.")
else:
    client.run(token)