import os
import re
from datetime import timedelta
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
APPLICATION_CHANNEL_ID = int(os.getenv("APPLICATION_CHANNEL_ID", "0"))
SUPPORT_CATEGORY_ID = int(os.getenv("SUPPORT_CATEGORY_ID", "0"))
SUPPORT_VOICE_CATEGORY_ID = int(os.getenv("SUPPORT_VOICE_CATEGORY_ID", "0"))

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing. Add it to a local .env file.")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

COLORS = {
    "blue": discord.Color.from_rgb(35, 115, 190),
    "green": discord.Color.from_rgb(45, 160, 105),
    "red": discord.Color.from_rgb(190, 55, 65),
}


def staff_allowed(member: discord.Member) -> bool:
    return member.guild_permissions.manage_channels or member.guild_permissions.administrator


def safe_channel_part(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9-]", "-", value.lower())
    return re.sub(r"-+", "-", cleaned).strip("-")[:35] or "member"


def configured_category(guild: discord.Guild, category_id: int) -> Optional[discord.CategoryChannel]:
    channel = guild.get_channel(category_id) if category_id else None
    return channel if isinstance(channel, discord.CategoryChannel) else None


async def get_or_create_support_voice(guild: discord.Guild) -> discord.VoiceChannel:
    existing = discord.utils.get(guild.voice_channels, name="suport")
    if existing:
        return existing
    return await guild.create_voice_channel(
        "suport",
        category=configured_category(guild, SUPPORT_VOICE_CATEGORY_ID),
        reason="Create support voice channel for staff assistance",
    )


async def send_ticket_panel(channel: discord.abc.Messageable) -> discord.Message:
    embed = discord.Embed(
        title="SCIENCE RP SUPPORT",
        description=(
            "Need help with the science department, server rules, or your roleplay application?\n\n"
            "Select an option below and our staff team will assist you."
        ),
        color=COLORS["blue"],
    )
    embed.add_field(name="Support ticket", value="Open a private ticket with the science RP staff.", inline=False)
    embed.add_field(name="Science application", value="Submit an application to join the science team.", inline=False)
    embed.set_footer(text="Science RP • Staff support center")
    return await channel.send(embed=embed, view=SupportPanel())


class ApplicationModal(discord.ui.Modal, title="Science Team Application"):
    age = discord.ui.TextInput(label="Age", placeholder="Your age", max_length=3, required=True)
    timezone = discord.ui.TextInput(
        label="Timezone and availability",
        placeholder="Example: UTC+1, evenings and weekends",
        max_length=200,
        required=True,
    )
    experience = discord.ui.TextInput(
        label="RP and science experience",
        placeholder="Tell us about your relevant experience",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=True,
    )
    motivation = discord.ui.TextInput(
        label="Why should we choose you?",
        placeholder="Explain your motivation for joining the science team",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Applications can only be submitted inside a server.", ephemeral=True)
            return
        review_channel = interaction.guild.get_channel(APPLICATION_CHANNEL_ID) if APPLICATION_CHANNEL_ID else None
        if not isinstance(review_channel, discord.TextChannel):
            await interaction.response.send_message(
                "The application review channel is not configured. Ask an administrator to set APPLICATION_CHANNEL_ID.",
                ephemeral=True,
            )
            return
        embed = discord.Embed(
            title="New Science Team Application",
            color=COLORS["green"],
            timestamp=discord.utils.utcnow(),
        )
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="Applicant", value=f"{interaction.user.mention}\n`{interaction.user.id}`", inline=False)
        embed.add_field(name="Age", value=self.age.value, inline=True)
        embed.add_field(name="Timezone and availability", value=self.timezone.value, inline=True)
        embed.add_field(name="RP and science experience", value=self.experience.value, inline=False)
        embed.add_field(name="Motivation", value=self.motivation.value, inline=False)
        await review_channel.send(embed=embed, view=ApplicationReviewView(interaction.user.id))
        await interaction.response.send_message("Your application was sent to the science staff team.", ephemeral=True)


class ApplicationReviewView(discord.ui.View):
    def __init__(self, applicant_id: int):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, custom_id="application_accept")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.finish(interaction, "accepted")

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger, custom_id="application_decline")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.finish(interaction, "declined")

    async def finish(self, interaction: discord.Interaction, result: str) -> None:
        if not isinstance(interaction.user, discord.Member) or not staff_allowed(interaction.user):
            await interaction.response.send_message("You need Manage Channels permission to review applications.", ephemeral=True)
            return
        applicant = interaction.guild.get_member(self.applicant_id) if interaction.guild else None
        if applicant and interaction.guild:
            try:
                await applicant.send(f"Your Science Team application in **{interaction.guild.name}** was {result}.")
            except discord.HTTPException:
                pass
        for child in self.children:
            child.disabled = True
        if interaction.message:
            await interaction.message.edit(view=self)
        await interaction.response.send_message(f"Application {result}.", ephemeral=True)


class SupportPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Open support ticket", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="open_support_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return
        existing = discord.utils.find(
            lambda channel: isinstance(channel, discord.TextChannel)
            and channel.topic == f"science-support:{interaction.user.id}",
            interaction.guild.text_channels,
        )
        if existing:
            await interaction.response.send_message(f"You already have a ticket: {existing.mention}", ephemeral=True)
            return
        bot_member = interaction.guild.me
        if bot_member is None:
            await interaction.response.send_message("The bot could not resolve its server permissions.", ephemeral=True)
            return
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            bot_member: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }
        channel = await interaction.guild.create_text_channel(
            f"ticket-{safe_channel_part(interaction.user.name)}",
            category=configured_category(interaction.guild, SUPPORT_CATEGORY_ID),
            topic=f"science-support:{interaction.user.id}",
            overwrites=overwrites,
            reason="Science RP support ticket",
        )
        embed = discord.Embed(
            title="SCIENCE RP TICKET",
            description="Explain your issue clearly. A staff member will respond as soon as possible.",
            color=COLORS["blue"],
        )
        await channel.send(content=interaction.user.mention, embed=embed, view=TicketControls())
        await interaction.response.send_message(f"Your private ticket is ready: {channel.mention}", ephemeral=True)

    @discord.ui.button(label="Apply for science team", style=discord.ButtonStyle.success, emoji="🧪", custom_id="open_science_application")
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(ApplicationModal())


class TicketControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_science_ticket")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not isinstance(interaction.channel, discord.TextChannel):
            return
        is_owner = interaction.channel.topic == f"science-support:{interaction.user.id}"
        is_staff = isinstance(interaction.user, discord.Member) and staff_allowed(interaction.user)
        if not (is_owner or is_staff):
            await interaction.response.send_message("Only the ticket owner or staff can close this ticket.", ephemeral=True)
            return
        await interaction.response.send_message("Closing this ticket in 3 seconds.")
        await discord.utils.sleep_until(discord.utils.utcnow() + timedelta(seconds=3))
        await interaction.channel.delete(reason="Science RP ticket closed")


@bot.tree.command(name="setup", description="Post the Science RP support and application panel")
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction) -> None:
    if interaction.channel is None:
        await interaction.response.send_message("Run this command in a server text channel.", ephemeral=True)
        return
    await send_ticket_panel(interaction.channel)
    await interaction.response.send_message("The Science RP panel was posted.", ephemeral=True)


@bot.tree.command(name="move_support", description="Move a member into the suport voice channel")
@app_commands.describe(member="The member to move into suport")
@app_commands.checks.has_permissions(manage_channels=True, move_members=True)
async def move_support(interaction: discord.Interaction, member: discord.Member) -> None:
    if not interaction.guild:
        await interaction.response.send_message("Use this command inside a server.", ephemeral=True)
        return
    if not member.voice:
        await interaction.response.send_message("That member is not connected to a voice channel.", ephemeral=True)
        return
    voice_channel = await get_or_create_support_voice(interaction.guild)
    await member.move_to(voice_channel, reason=f"Moved to suport by {interaction.user}")
    await interaction.response.send_message(f"Moved {member.mention} to {voice_channel.mention}.", ephemeral=True)


@bot.tree.command(name="close_ticket", description="Close the current Science RP ticket")
@app_commands.checks.has_permissions(manage_channels=True)
async def close_ticket(interaction: discord.Interaction) -> None:
    channel = interaction.channel
    if not isinstance(channel, discord.TextChannel) or not channel.topic or not channel.topic.startswith("science-support:"):
        await interaction.response.send_message("This command can only be used in a science support ticket.", ephemeral=True)
        return
    await interaction.response.send_message("Closing this ticket in 3 seconds.")
    await discord.utils.sleep_until(discord.utils.utcnow() + timedelta(seconds=3))
    await channel.delete(reason="Science RP ticket closed")


@bot.event
async def on_ready() -> None:
    bot.add_view(SupportPanel())
    bot.add_view(TicketControls())
    try:
        synced = await bot.tree.sync()
        print(f"Logged in as {bot.user} | synced {len(synced)} commands")
    except discord.HTTPException as error:
        print(f"Command sync failed: {error}")


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
    if isinstance(error, app_commands.MissingPermissions):
        message = "You do not have permission to use this command."
    else:
        message = "The command could not be completed. Check the bot permissions and configuration."
        print(f"Application command error: {error}")
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


bot.run(TOKEN)
