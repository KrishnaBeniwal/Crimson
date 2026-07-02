import discord
from discord.ext import commands
from discord import app_commands

class Invite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="invite")
    async def invite_prefix(self, ctx):
        """Sends the bot invite link."""
        # Build the OAuth2 invite link.
        invite_link = "https://discord.com/oauth2/authorize?client_id=1479231849225261107&permissions=8&integration_type=0&scope=bot+applications.commands"
        await ctx.send(f"**Invite me:** {invite_link}\n```\n{invite_link}\n```")

    @app_commands.command(name="invite", description="Sends the bot invite link")
    async def invite_slash(self, interaction: discord.Interaction):
        invite_link = "https://discord.com/oauth2/authorize?client_id=1479231849225261107&permissions=8&integration_type=0&scope=bot+applications.commands"
        await interaction.response.send_message(f"**Invite me:** {invite_link}\n```\n{invite_link}\n```")

async def setup(bot):
    await bot.add_cog(Invite(bot))
