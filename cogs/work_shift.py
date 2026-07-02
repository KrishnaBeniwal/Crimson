import discord
from discord.ext import commands
import re
import asyncio

# Keep track of active work shifts.
WORK_MEMORY = {}

# Keep track of background tasks.
_ws_background_tasks: set[asyncio.Task] = set()

DANK_MEMER_ID = 270904126974590976
EMPTYSPACE_REGEX = re.compile(r'<a?:emptyspace:\d+>|:emptyspace:', re.IGNORECASE)
BASKETBALL_REGEX = re.compile(r'<a?:basketball:\d+>|:basketball:|🏀', re.IGNORECASE)
GOALKEEPER_REGEX = re.compile(r'<a?:levitate:\d+>|:levitate:|🕴️|🕴', re.IGNORECASE)

# Time until an active work shift expires.
_WORK_MEMORY_TTL = 120


def _track_ws_task(task: asyncio.Task):
    """Add task to tracking set and auto-remove on completion."""
    _ws_background_tasks.add(task)
    task.add_done_callback(_ws_background_tasks.discard)


async def _expire_work_memory(msg_id: int):
    """Auto-remove a WORK_MEMORY entry after TTL to prevent leaks."""
    await asyncio.sleep(_WORK_MEMORY_TTL)
    WORK_MEMORY.pop(msg_id, None)


def get_embed_text(embed: discord.Embed):
    parts = [embed.title or "", embed.description or ""]
    for field in embed.fields:
        parts.append(field.name or "")
        parts.append(field.value or "")
    return "\n".join(part for part in parts if part)


def _get_position_from_marker(line: str, marker_regex: re.Pattern):
    """Shared helper: determine left/middle/right from a marker emoji position in a line."""
    marker = marker_regex.search(line)
    if not marker:
        return None

    left_part = line[:marker.start()]
    emptyspace_count = len(EMPTYSPACE_REGEX.findall(left_part))

    if emptyspace_count >= 2:
        return "right"
    if emptyspace_count == 1:
        return "middle"
    return "left"


def get_goalkeeper_position(desc: str):
    for line in desc.split('\n'):
        pos = _get_position_from_marker(line.strip(), GOALKEEPER_REGEX)
        if pos:
            return pos
    return None


def get_basketball_position(desc: str):
    for line in desc.split('\n'):
        pos = _get_position_from_marker(line.strip(), BASKETBALL_REGEX)
        if pos:
            return pos
    return None


class WorkShift(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id != DANK_MEMER_ID or not message.embeds:
            return

        # Stop if the guild opted out of tracking.
        if message.guild:
            privacy_cog = self.bot.get_cog("Privacy")
            if privacy_cog and privacy_cog.is_guild_opted_out(message.guild.id):
                return

        embed = message.embeds[0]
        desc = embed.description or ""
        embed_text = get_embed_text(embed)

        # Handle the color match minigame.
        if "Look at each color next to the words closely!" in desc:
            color_map = {}
            for line in desc.split('\n'):
                # Extract emojis and their corresponding words.
                match = re.search(r'<a?:([a-zA-Z0-9_]+):\d+>\s*([^\s]+)', line)
                if match:
                    emoji_name = match.group(1).lower()
                    word = match.group(2).strip().lower()
                    color_map[word] = emoji_name
            
            if color_map:
                lines = [f"{color} {word}" for word, color in color_map.items()]
                initial_answer = "\n".join(lines)
                try:
                    await message.add_reaction("<a:Verified_tick:1501475360791990342>")
                    reply_msg = await message.channel.send(initial_answer)
                    WORK_MEMORY[message.id] = {
                        "type": "color_match",
                        "data": color_map,
                        "reply_msg": reply_msg
                    }
                    task = asyncio.create_task(_expire_work_memory(message.id))
                    _track_ws_task(task)
                except Exception:
                    pass

        elif "Remember words order!" in desc:
            words = []
            for line in desc.split('\n'):
                match = re.search(r'`([^`]+)`', line)
                if match:
                    words.append(match.group(1).strip())
            
            if words:
                formatted_words = [f"`{w}`" for w in words]
                answer = "\n".join(formatted_words)
                try:
                    await message.channel.send(answer)
                    await message.add_reaction("<a:Verified_tick:1501475360791990342>")
                except Exception:
                    pass

        elif "Look at the emoji closely!" in desc:
            emoji = desc.replace("Look at the emoji closely!", "").strip()
            
            if emoji:
                try:
                    await message.add_reaction("<a:Verified_tick:1501475360791990342>")
                    reply_msg = await message.channel.send(emoji)
                    WORK_MEMORY[message.id] = {
                        "type": "emoji_match",
                        "data": emoji,
                        "reply_msg": reply_msg
                    }
                    task = asyncio.create_task(_expire_work_memory(message.id))
                    _track_ws_task(task)
                except Exception:
                    pass

        elif "Dunk the ball!" in embed_text:
            position = get_basketball_position(embed_text)
            
            if position:
                try:
                    reply_msg = await message.channel.send(f"click - ``{position}``")
                    WORK_MEMORY[message.id] = {
                        "type": "dunk_the_ball",
                        "reply_msg": reply_msg
                    }
                    task = asyncio.create_task(_expire_work_memory(message.id))
                    _track_ws_task(task)
                except Exception:
                    pass

        elif "Hit the ball!" in embed_text:
            position = get_goalkeeper_position(embed_text)
            
            if position:
                try:
                    reply_msg = await message.channel.send(f"goalkeeper position - ``{position}``")
                    WORK_MEMORY[message.id] = {
                        "type": "hit_the_ball",
                        "reply_msg": reply_msg
                    }
                    task = asyncio.create_task(_expire_work_memory(message.id))
                    _track_ws_task(task)
                except Exception:
                    pass

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if after.id not in WORK_MEMORY:
            return

        game_info = WORK_MEMORY[after.id]
        
        desc = ""
        if after.embeds:
            desc = after.embeds[0].description or ""
            embed_text = get_embed_text(after.embeds[0])
        else:
            embed_text = ""
        content = after.content or ""
        
        full_text = embed_text + "\n" + content

        if game_info["type"] == "color_match":
            if "What color was next to the word" in full_text:
                match = re.search(r'What color was next to the word\s+([^\?]+)\?', full_text, re.IGNORECASE)
                if match:
                    target_word = match.group(1).replace('`', '').strip().lower()
                    color_map = game_info["data"]
                    reply_msg = game_info.get("reply_msg")
                    
                    if target_word in color_map:
                        answer = color_map[target_word]
                        try:
                            if reply_msg:
                                await reply_msg.edit(content=answer)
                                await reply_msg.add_reaction("<a:Verified_tick:1501475360791990342>")
                            else:
                                await after.channel.send(answer)
                                await after.add_reaction("<a:Verified_tick:1501475360791990342>")
                        except Exception:
                            pass
                
                # Remove the completed minigame from memory.

        elif game_info["type"] == "dunk_the_ball":
            if "Dunk the ball!" in full_text:
                position = get_basketball_position(full_text)
                
                if position:
                    formatted_msg = f"click - ``{position}``"
                    try:
                        reply_msg = game_info.get("reply_msg")
                        if reply_msg and reply_msg.content != formatted_msg:
                            await reply_msg.edit(content=formatted_msg)
                    except Exception:
                        pass
            else:
                # Clear memory if the game is over.
                WORK_MEMORY.pop(after.id, None)

        elif game_info["type"] == "hit_the_ball":
            if "Hit the ball!" in full_text:
                position = get_goalkeeper_position(full_text)
                
                if position:
                    formatted_msg = f"goalkeeper position - ``{position}``"
                    try:
                        reply_msg = game_info.get("reply_msg")
                        if reply_msg and reply_msg.content != formatted_msg:
                            await reply_msg.edit(content=formatted_msg)
                    except Exception:
                        pass
            else:
                # Clear memory if the game is over.
                WORK_MEMORY.pop(after.id, None)



async def setup(bot):
    await bot.add_cog(WorkShift(bot))
