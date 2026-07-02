import discord
from discord.ext import commands
import io

LOG_CHANNEL_ID = 1521584987361775849

async def build_server_data(bot, guild: discord.Guild, is_fresh=False):
    # Check audit logs to find who added the bot.
    added_by = "Unknown (Missing Permissions)"
    if guild.me.guild_permissions.view_audit_log:
        try:
            async for entry in guild.audit_logs(limit=20, action=discord.AuditLogAction.bot_add):
                if entry.target and entry.target.id == bot.user.id:
                    added_by = f"{entry.user} ({entry.user.id})"
                    break
            else:
                added_by = "Unknown (Not in recent logs)"
        except Exception:
            added_by = "Unknown (Error reading logs)"

    # Create a permanent invite link if possible.
    invite_url = "Missing Permissions / No Channels"
    if guild.me.guild_permissions.create_instant_invite:
        try:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).create_instant_invite:
                    invite = await channel.create_invite(max_age=0, max_uses=0, reason="Join Logger Permanent Invite")
                    invite_url = invite.url
                    break
        except Exception:
            invite_url = "Error creating invite"

    embed = discord.Embed(
        title=f"{'[FRESH] ' if is_fresh else ''}Joined Server: {guild.name}",
        color=discord.Color.brand_green() if not is_fresh else discord.Color.blurple()
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
        
    owner_str = f"{guild.owner} ({guild.owner_id})" if guild.owner else str(guild.owner_id)
    embed.add_field(name="Owner", value=owner_str, inline=False)
    embed.add_field(name="Added By", value=added_by, inline=False)
    
    joined_at_str = f"<t:{int(guild.me.joined_at.timestamp())}:F>" if guild.me and guild.me.joined_at else "Unknown"
    embed.add_field(name="Joined At", value=joined_at_str, inline=False)
    
    embed.add_field(name="Member Count", value=f"{guild.member_count}", inline=False)
    embed.add_field(name="Permanent Invite", value=invite_url, inline=False)
    
    embed.set_footer(text=f"Server ID: {guild.id}")
    
    return embed

class RefreshDataView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    async def _get_guild(self, interaction: discord.Interaction):
        if not interaction.message.embeds:
            await interaction.followup.send("Could not find server info in this message.", ephemeral=True)
            return None
            
        embed = interaction.message.embeds[0]
        guild_id_str = embed.footer.text.replace("Server ID: ", "") if embed.footer else ""
        try:
            guild_id = int(guild_id_str.strip())
        except ValueError:
            await interaction.followup.send("Invalid Server ID in embed.", ephemeral=True)
            return None
            
        guild = self.bot.get_guild(guild_id)
        if not guild:
            await interaction.followup.send("I am no longer in that server or it doesn't exist.", ephemeral=True)
            return None
            
        return guild

    @discord.ui.button(label="Get Fresh Data", style=discord.ButtonStyle.primary, custom_id="join_log:get_fresh_data")
    async def get_fresh_data(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=False, thinking=True)
        guild = await self._get_guild(interaction)
        if not guild: return
            
        embed = await build_server_data(self.bot, guild, is_fresh=True)
        await interaction.followup.send(embed=embed)

    @discord.ui.button(label="Get Members List", style=discord.ButtonStyle.secondary, custom_id="join_log:get_members")
    async def get_members_list(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=False, thinking=True)
        guild = await self._get_guild(interaction)
        if not guild: return
        
        # Fetch the full member list only when requested.
        if not guild.chunked:
            try:
                await guild.chunk()
            except Exception:
                pass
        
        members_text = f"Members of {guild.name} (ID: {guild.id})\n"
        bot_count = sum(1 for m in guild.members if m.bot)
        members_text += f"Total Count: {guild.member_count} | Humans: {guild.member_count - bot_count} | Bots: {bot_count}\n"
        members_text += "-" * 40 + "\n"
        
        for member in guild.members:
            members_text += f"{member} ({member.id}) {'[BOT]' if member.bot else ''}\n"
            
        file_bytes = io.BytesIO(members_text.encode('utf-8'))
        txt_file = discord.File(file_bytes, filename=f"members_{guild.id}.txt")
        await interaction.followup.send(content=f"Here is the member list for **{guild.name}**:", file=txt_file)

class JoinLogger(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(RefreshDataView(self.bot))
        
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            try:
                log_channel = await self.bot.fetch_channel(LOG_CHANNEL_ID)
            except Exception:
                return
                
        embed = await build_server_data(self.bot, guild, is_fresh=False)
        view = RefreshDataView(self.bot)
        
        try:
            await log_channel.send(embed=embed, view=view)
        except Exception as e:
            print(f"Failed to send join log: {e}")

async def setup(bot):
    await bot.add_cog(JoinLogger(bot))
