import discord
from discord.ext import commands
from discord import app_commands

def parse_color(color_str: str) -> discord.Color:
    # Handle missing or default colors.
    if not color_str:
        return discord.Color.default()
        
    color_str = color_str.strip().lower()
    
    if hasattr(discord.Color, color_str) and callable(getattr(discord.Color, color_str)):
        try:
            return getattr(discord.Color, color_str)()
        except:
            pass
            
    if color_str.startswith('#'):
        color_str = color_str[1:]
    
    if len(color_str) == 6:
        try:
            return discord.Color(int(color_str, 16))
        except ValueError:
            pass
            
    if ',' in color_str:
        parts = color_str.replace('(', '').replace(')', '').split(',')
        if len(parts) == 3:
            try:
                r, g, b = [int(p.strip()) for p in parts]
                return discord.Color.from_rgb(r, g, b)
            except ValueError:
                pass
                
    return discord.Color.default()

class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="createrole")
    @commands.has_permissions(manage_roles=True)
    async def createrole_prefix(self, ctx, *, roles_data: str):
        created_roles = []
        roles_list = [r.strip() for r in roles_data.split(',')]
        
        for role_entry in roles_list:
            if not role_entry: continue
            
            parts = role_entry.split(':', 1)
            name = parts[0].strip()
            color_str = parts[1].strip() if len(parts) > 1 else None
            
            parsed_color = parse_color(color_str) if color_str else discord.Color.default()
            try:
                role = await ctx.guild.create_role(name=name, color=parsed_color)
                created_roles.append(f"**{role.name}**")
            except discord.Forbidden:
                await ctx.send("❌ I do not have permission to create roles.")
                return
            except Exception as e:
                await ctx.send(f"❌ Error creating role '{name}': {e}")
                return
                
        if created_roles:
            await ctx.send(f"✅ Successfully created {len(created_roles)} roles: {', '.join(created_roles)}")

    @app_commands.command(name="createrole", description="Create multiple new roles at once")
    @app_commands.describe(roles_data="Format: RoleName:Color, RoleName2:Color (e.g. Admin:red, Member)")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def createrole_slash(self, interaction: discord.Interaction, roles_data: str):
        await interaction.response.defer(ephemeral=False)
        created_roles = []
        roles_list = [r.strip() for r in roles_data.split(',')]
        
        for role_entry in roles_list:
            if not role_entry: continue
            
            parts = role_entry.split(':', 1)
            name = parts[0].strip()
            color_str = parts[1].strip() if len(parts) > 1 else None
            
            parsed_color = parse_color(color_str) if color_str else discord.Color.default()
            try:
                role = await interaction.guild.create_role(name=name, color=parsed_color)
                created_roles.append(f"**{role.name}**")
            except discord.Forbidden:
                await interaction.followup.send("❌ I do not have permission to create roles.")
                return
            except Exception as e:
                await interaction.followup.send(f"❌ Error creating role '{name}': {e}")
                return
                
        if created_roles:
            await interaction.followup.send(f"✅ Successfully created {len(created_roles)} roles: {', '.join(created_roles)}")

    @commands.command(name="roleids", aliases=["giveroleid", "roleid"])
    async def roleids_prefix(self, ctx, *, roles_data: str):
        # Look up roles by ping, ID, or name.
        role_names = [r.strip().lower() for r in roles_data.split(',')]
        found_roles = []
        
        for r_name in role_names:
            if not r_name: continue
            
            r_id = None
            if r_name.startswith('<@&') and r_name.endswith('>'):
                try:
                    r_id = int(r_name[3:-1])
                except: pass
            elif r_name.isdigit():
                r_id = int(r_name)
                
            role = None
            if r_id:
                role = ctx.guild.get_role(r_id)
                
            if not role:
                role = discord.utils.find(lambda r: r.name.lower() == r_name, ctx.guild.roles)
                
            if role and role not in found_roles:
                found_roles.append(role)
                
        if not found_roles:
            await ctx.send("❌ Could not find any roles matching your input.")
            return
            
        response = "\n".join([f"{role.name}: {role.id}" for role in found_roles])
        await ctx.send(f"**Role IDs:**\n```\n{response}\n```")

    @app_commands.command(name="roleids", description="Get the IDs of up to 5 roles at once in a copyable format")
    @app_commands.describe(role1="First role", role2="Second role (optional)", role3="Third role (optional)", role4="Fourth role (optional)", role5="Fifth role (optional)")
    async def roleids_slash(self, interaction: discord.Interaction, role1: discord.Role, role2: discord.Role = None, role3: discord.Role = None, role4: discord.Role = None, role5: discord.Role = None):
        roles = [r for r in [role1, role2, role3, role4, role5] if r is not None]
        
        response = "\n".join([f"{role.name}: {role.id}" for role in roles])
        await interaction.response.send_message(f"**Role IDs:**\n```\n{response}\n```", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Roles(bot))
