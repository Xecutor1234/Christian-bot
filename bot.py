import discord
import os
from keep_alive import keep_alive
import requests
from replit import db
# These imports were missing from the previous reset, my apologies.
from google.generativeai.generative_models import GenerativeModel
from urllib.parse import quote

# --- BOT SETUP ---
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

# We will use the basic discord.Client for maximum stability
client = discord.Client(intents=intents)

# --- DATABASE HELPER FUNCTIONS ---
def set_prayer_log_channel(guild_id: int, channel_id: int):
    db[f"prayer_log_{guild_id}"] = str(channel_id)

def get_prayer_log_channel(guild_id: int):
    return db.get(f"prayer_log_{guild_id}")

# --- PRAYER REQUEST UI COMPONENTS (STABLE SYNTAX) ---
class PrayerRequestModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(title="Submit a Prayer Request", *args, **kwargs)
        self.add_item(discord.ui.InputText(
            label="What can we pray for you about?",
            style=discord.TextStyle.paragraph,
            placeholder="Please share your request here. It will be sent privately.",
        ))

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild_id:
            return # Should not happen from a server button

        log_channel_id_str = get_prayer_log_channel(interaction.guild_id)
        if not log_channel_id_str:
            await interaction.response.send_message('The prayer system is not set up correctly.', ephemeral=True)
            return

        log_channel = client.get_channel(int(log_channel_id_str))

        if isinstance(log_channel, discord.TextChannel):
            embed = discord.Embed(title="New Prayer Request", description=self.children[0].value, color=discord.Color.blue())
            embed.set_author(name=f"From: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text=f"User ID: {interaction.user.id}")

            await log_channel.send(embed=embed)
            await interaction.response.send_message('Thank you. Your prayer request has been received.', ephemeral=True)
        else:
            await interaction.response.send_message('Configuration error: The prayer log channel is invalid.', ephemeral=True)

class PrayerRequestView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Request Prayer', style=discord.ButtonStyle.primary, custom_id='prayer_request_button_persistent')
    async def button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(PrayerRequestModal())

# --- BOT EVENTS ---
@client.event
async def on_ready():
    # Register the persistent view so the button works after restarts
    client.add_view(PrayerRequestView())
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # --- PRAYER REQUEST SETUP COMMAND ---
    if message.content.startswith('!setup_prayer'):
        if not message.author.guild_permissions.administrator:
            await message.channel.send("You need to be an administrator to run this command.", delete_after=10)
            return

        parts = message.content.split()
        if len(parts) != 3 or not parts[1].startswith('<#') or not parts[2].startswith('<#'):
            await message.channel.send("Usage: `!setup_prayer #public-channel #log-channel`", delete_after=10)
            return

        try:
            public_channel_id = int(parts[1][2:-1])
            log_channel_id = int(parts[2][2:-1])

            public_channel = client.get_channel(public_channel_id)
            log_channel = client.get_channel(log_channel_id)

            if not isinstance(public_channel, discord.TextChannel) or not isinstance(log_channel, discord.TextChannel):
                raise ValueError("Invalid channel provided.")

            set_prayer_log_channel(message.guild.id, log_channel.id)

            embed = discord.Embed(
                title="Prayer Requests",
                description="If you have a prayer request, please click the button below. Your submission will be completely private.",
                color=discord.Color.gold()
            )
            await public_channel.send(embed=embed, view=PrayerRequestView())
            await message.channel.send(f"Success! Prayer button posted in {public_channel.mention} and logs will be sent to {log_channel.mention}.", delete_after=10)
            await message.delete()

        except (ValueError, IndexError):
            await message.channel.send("Error: Please make sure you mention two valid text channels.", delete_after=10)
        return

    # --- OTHER FEATURES ---
    is_server_channel = isinstance(message.channel, discord.TextChannel)
    is_dm_channel = isinstance(message.channel, discord.DMChannel)

    # Image Generation
    if is_server_channel and message.channel.name == 'christian-ai-image-generation🎨':
        # ... (Your image logic here)
        return

    # AI Chat
    if (is_server_channel and message.channel.name == 'chat-with-christian-bot') or is_dm_channel:
        # ... (Your AI chat logic here)
        return

    # Simple Commands
    if message.content.startswith('!ping'):
        await message.channel.send('Pong!')
        return

# ... (We can add dailyverse back if needed, I've removed it to simplify for now) ...

# --- Keep Alive and Bot Run Logic ---
keep_alive()

token = os.getenv('DISCORD_TOKEN')
if token is None:
    print("CRITICAL ERROR: DISCORD_TOKEN secret is not found.")
else:
    client.run(token)