######################################
##### Created by @paidbycrypto. ######
######################################

##############################################
##### Configurate the bot in config.json #####
##############################################

import discord
from discord.ext import commands
import json
from discord.ui import Select, View, Button
import os
from discord import app_commands
import sys
import datetime
import chat_exporter

with open('config.json', 'r') as f:
    config = json.load(f)

if not os.path.exists('transcripts'):
    os.makedirs('transcripts')
    
intents = discord.Intents.all()
intents.message_content = True

bot = commands.Bot(command_prefix="$", intents=intents)

ALLOWED_CATEGORIES = [int(category_id) for category_id in config['categories'].values()]
ALLOWED_ROLES = [int(config['staff_role_id'])]
ROLE_TO_PING = int(config['role_to_ping_id'])
TRANSCRIPT_CHANNEL = int(config["transcript_channel_id"])
FOOTER_TEXT = config['footer_text']
IMAGE_URL = config['image_url']
THUMB_URL = config['thumb_url']


class TicketPanel:
    def __init__(self):
        self.embed = discord.Embed(
            title="Ticket Panel",
            description="**Ticket Rules:**\n- Do not ping Team Members.\n- Specify what do you need.\n- Follow all instructions from our Team Members.",
            color=discord.Color.blue()
        )
        self.embed.set_footer(text=f"{FOOTER_TEXT}")
        self.embed.set_image(url=f"{IMAGE_URL}")
        self.embed.set_thumbnail(url=f"{THUMB_URL}")

        self.select = Select(
            placeholder="Choose a ticket category...",
            options=[
                discord.SelectOption(label="General Enquires", value="support"),
                discord.SelectOption(label="Billing Ticket", value="bug"),
                discord.SelectOption(label="Technical Support", value="feature"),
                discord.SelectOption(label="Other", value="other")
            ]
        )

    def get_embed(self):
        return self.embed

    def get_select(self):
        return self.select


async def clear_panel_channel():
    channel = bot.get_channel(int(config['panel_channel_id']))
    if channel:
        await channel.purge()
        print(f"Cleared all messages in channel {channel.name}")

async def send_ticket_panel():
    channel = bot.get_channel(int(config['panel_channel_id']))
    if not channel:
        print("Panel channel not found!")
        return

    await clear_panel_channel()

    ticket_panel = TicketPanel()

    embed = ticket_panel.get_embed()
    select = ticket_panel.get_select()

    async def select_callback(interaction):
        selected_option = select.values[0]
        category_id = config['categories'].get(selected_option)

        if not category_id:
            await interaction.response.send_message("Invalid category selected!", ephemeral=True)
            return

        category = discord.utils.get(interaction.guild.categories, id=int(category_id))
        
        if category is None:
            await interaction.response.send_message(f"Category with ID {category_id} not found.", ephemeral=True)
            return

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True) 
        }

        new_channel = await interaction.guild.create_text_channel(
            f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )

        await new_channel.send(f"|| <@&{ROLE_TO_PING}> ||", delete_after=3)

        embed = discord.Embed(
            title="**Hello!**",
            description="Please specify your question or issue, and one of our support members will assist you shortly.",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"{FOOTER_TEXT}")
        embed.set_image(url=f"{IMAGE_URL}")
        embed.set_thumbnail(url=f"{THUMB_URL}")
        

        close_button = Button(label="Close Ticket", style=discord.ButtonStyle.danger)

        async def close_button_callback(interaction):
            await new_channel.edit(name=f"closed-{interaction.user.name}")

            for member in new_channel.guild.members:
                await new_channel.set_permissions(member, view_channel=False)
                
            embed = discord.Embed(
                title="Ticket Closed!",
                description="This ticket has been successfully closed.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"{FOOTER_TEXT}")
            embed.set_image(url=f"{IMAGE_URL}")
            embed.set_thumbnail(url=f"{THUMB_URL}")
        
            await new_channel.send(embed=embed)

            await interaction.response.send_message(f"Your ticket has been closed: <#{new_channel.id}>", ephemeral=True)

        close_button.callback = close_button_callback
        view = View(timeout=None)
        view.add_item(close_button)

        await new_channel.send(embed=embed, view=view)

        await interaction.response.send_message(
            f"Your ticket has been created: <#{new_channel.id}>",
            ephemeral=True
        )

    select.callback = select_callback

    view = View(timeout=None)
    view.add_item(select)

    await channel.send(embed=embed, view=view)


async def generate_and_send_transcript(channel: discord.TextChannel, bot: commands.Bot):
    transcript_channel_id = int(config["transcript_channel_id"])

    transcript = await chat_exporter.export(channel)

    if transcript is None:
        return "Failed to generate transcript."

    now = datetime.datetime.now()
    filename = f"transcript_{channel.name}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.html"

    file_path = os.path.join('transcripts', filename)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(transcript)

    transcript_channel = bot.get_channel(transcript_channel_id)

    if transcript_channel:
        with open(file_path, "rb") as file:
            await transcript_channel.send(f"Here is the transcript of {channel.name}:", file=discord.File(file, filename))

        return f"Transcript saved and sent to <#{transcript_channel_id}>."

    else:
        return "Could not find the specified transcript channel."

    
@bot.tree.command(name="delete", description="Delete the ticket channel.")
async def delete_ticket(interaction: discord.Interaction):
    channel = interaction.channel

    if not any(role.id == int(config['staff_role_id']) for role in interaction.user.roles):
        await interaction.response.send_message("You do not have permission to delete tickets.", ephemeral=True)
        return
    
    allowed_categories = [int(config["categories"]["support"]), 
                          int(config["categories"]["bug"]), 
                          int(config["categories"]["feature"]), 
                          int(config["categories"]["other"])]
    
    print(f"Channel category_id: {channel.category_id}")
    print(f"Allowed categories: {allowed_categories}")

    if channel.category_id not in allowed_categories:
        await interaction.response.send_message("You can only delete channels in the designated ticket categories.", ephemeral=True)
        return

    bot = interaction.client
    result_message = await generate_and_send_transcript(channel, bot)
    
    await interaction.response.send_message(result_message, ephemeral=True)
    
    await channel.delete(reason="Ticket deleted by staff.")

    
@bot.tree.command(name="restart", description="Restart the bot.")
async def restart_bot(interaction: discord.Interaction):
    if not any(role.id == int(config['staff_role_id']) for role in interaction.user.roles):
        await interaction.response.send_message("You do not have permission to restart the bot.", ephemeral=True)
        return

    await interaction.response.send_message("Restarting bot...", ephemeral=True)

    os.execv(sys.executable, ['python'] + sys.argv)
    
  

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()
    await send_ticket_panel()

bot.run(config['token'])
