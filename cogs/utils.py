import discord
from discord.ext import commands
from discord import app_commands
from dank_data import ANAGRAM_KNOWLEDGE

class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def do_unscramble(self, text: str):
        # Sort letters alphabetically to find anagram matches.
        sorted_scramble = "".join(sorted(text.lower().replace(" ", "")))
        if sorted_scramble in ANAGRAM_KNOWLEDGE:
            return ANAGRAM_KNOWLEDGE[sorted_scramble]
        return None

    @commands.command(name="unscramble")
    async def unscramble_prefix(self, ctx, *, text: str):
        """Unscrambles a string of text to find Dank Memer items."""
        ans = self.do_unscramble(text)
        if ans:
            await ctx.send(f"Unscrambled: **{ans}**\n``{ans}``\n```{ans}```")
        else:
            await ctx.send("Could not find a matching item in the database for those letters.")

    @app_commands.command(name="unscramble", description="Unscramble a string of text to find Dank Memer items")
    @app_commands.describe(text="The scrambled text to solve")
    async def unscramble_slash(self, interaction: discord.Interaction, text: str):
        ans = self.do_unscramble(text)
        if ans:
            await interaction.response.send_message(f"Unscrambled: **{ans}**\n``{ans}``\n```{ans}```")
        else:
            await interaction.response.send_message("Could not find a matching item in the database for those letters.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Utils(bot))
