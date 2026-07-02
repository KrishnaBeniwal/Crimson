import discord
from discord.ext import commands
import os
import re
import asyncio
from dotenv import load_dotenv
from dank_data import REVERSE_KNOWLEDGE, ANAGRAM_KNOWLEDGE

# Load the bot token.
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

PREFIX = "crim " 

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

DANK_MEMER_ID = 270904126974590976
EXCLUDED_SERVER_ID = 1438233304867278870
POOKIE_MOD_ROLE_ID = 1442608832416321578

RANDOM_XP_EVENTS_ID = 1494299552428326912
RANDOM_GAY_EVENTS_ID = 1494299597206720602
RANDOM_FIH_EVENTS_ID = 1494299665645043804
RANDOM_XP_AND_LUCK_BOOST_ID = 1494304732473200765

CHANNEL_MAP = {
    "Dank Scrambled Eggs": RANDOM_XP_EVENTS_ID,
    "Steal Mel's Beard": RANDOM_XP_EVENTS_ID,
    "Boss Battle": RANDOM_XP_EVENTS_ID,
    "Fortnite Attack": RANDOM_XP_EVENTS_ID,
    "Reverse Reverse": RANDOM_GAY_EVENTS_ID,
    "Item Guesser": RANDOM_GAY_EVENTS_ID,
    "Dice Champs": RANDOM_GAY_EVENTS_ID,
    "Anti-Rizz": RANDOM_GAY_EVENTS_ID,
    "Fortnite Dance Mode": RANDOM_GAY_EVENTS_ID,
    "Dank Memer Corp": RANDOM_GAY_EVENTS_ID,
    "Skibidi Defense": RANDOM_GAY_EVENTS_ID,  
    "Punch Pepe": RANDOM_GAY_EVENTS_ID,
    "Fish Invasion": RANDOM_FIH_EVENTS_ID,
    "Fish Guesser": RANDOM_FIH_EVENTS_ID,
    "Mythical Fish": RANDOM_FIH_EVENTS_ID,
    "Luck Boost": RANDOM_XP_AND_LUCK_BOOST_ID,
    "Double XP": RANDOM_XP_AND_LUCK_BOOST_ID,
}

EVENT_ROLE_MAP = {
    "Dank Scrambled Eggs": 1501284776823488635,
    "Steal Mel's Beard": 1501284779163910164,
    "Boss Battle": 1501284781340626956,
    "Fortnite Attack": 1501284784721367191,
    "Reverse Reverse": 1501284789158678630,
    "Item Guesser": 1501284792165990585,
    "Dice Champs": 1501284794171133962,
    "Anti-Rizz": 1501284795794329812,
    "Fortnite Dance Mode": 1501284798184820928,
    "Dank Memer Corp": 1501284799959269449,
    "Skibidi Defense": 1501284802740093059,  
    "Punch Pepe": 1501284805835362384,
    "Fish Invasion": 1501284808381431898,
    "Fish Guesser": 1501284810679779559,
    "Mythical Fish": 1501284812789383392,
    "Luck Boost": 1501284816274980884,
    "Double XP": 1501284818653151445,
}

# Cache active events and state for quick lookups.
GUESSER_MEMORY = {}  
INVITE_CACHE = {}    
ACTIVE_EVENTS_BY_MSG_ID = {}
ACTIVE_EVENTS_BY_CHANNEL_TITLE = {}

# Keep track of active tasks.
_background_tasks: set[asyncio.Task] = set()

def _track_task(task: asyncio.Task):
    """Add task to tracking set and auto-remove on completion."""
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

async def clear_event_cache(msg_id, channel_title_tuple, timeout_seconds):
    """Wait for the timeout and then clear the event from memory to prevent memory leaks."""
    await asyncio.sleep(timeout_seconds)
    ACTIVE_EVENTS_BY_MSG_ID.pop(msg_id, None)
    ACTIVE_EVENTS_BY_CHANNEL_TITLE.pop(channel_title_tuple, None)

IMAGE_ID_REGEX = re.compile(r'(\d+)\.(?:png|webp|gif)')
SAY_QUOTE_REGEX = re.compile(r'say "(.*?)"')
ARROW_REGEX = re.compile(r'Arrow(Up|Down|Left|Right)ui', re.IGNORECASE)

_RE_SUCCESSFULLY = re.compile(r'^(.*?)\s+successfully\s+', re.IGNORECASE)
_RE_WON = re.compile(r'^(.*?)\s+won\s+', re.IGNORECASE)
_RE_RECEIVED = re.compile(r'^(.*?)\s+received:', re.IGNORECASE)

# Detect event outcomes, checking failures first since they are more common.
_RESULT_PHRASES = (
    ("not enough people joined", False),
    ("not enough players rolled the dice", False),
    ("the correct answer was", False),
    ("the correct answer version was", False),
    ("the correct reversed version was", False),
    ("no one wanted to steal", False),
    ("no one wanted to punch pepe", False),
    ("no one wanted to defend", False),
    ("no one was able to type", False),
    ("nobody answered", False),
    # --- Successes ---
    ("has been defeated!", True),
    ("congrats, you now work for fortnite", True),
    ("congrats, you now get your dank memer corp", True),
    ("is now yours", True),
    ("better luck next time", True),
    (" received:", True),
    ("successfully", True),
    ("reward", True),
)

# Phrases that require two keywords to match.
_RESULT_PAIR_PHRASES = (
    ("you typed", "correctly!", True),
    ("you guessed", "correctly!", True),
    ("won", "coins", True),
)

def _classify_result(text: str):
    """Classify embed text as (is_result, is_success). Returns (False, False) if not a result."""
    for phrase, success in _RESULT_PHRASES:
        if phrase in text:
            return True, success
    for kw1, kw2, success in _RESULT_PAIR_PHRASES:
        if kw1 in text and kw2 in text:
            return True, success
    return False, False


def extract_image_id(url):
    match = IMAGE_ID_REGEX.search(url)
    return match.group(1) if match else None

@bot.event
async def setup_hook():
    await bot.load_extension("cogs.invite")
    await bot.load_extension("cogs.access")
    await bot.load_extension("cogs.roles")
    await bot.load_extension("cogs.channels")
    await bot.load_extension("cogs.work_shift")
    await bot.load_extension("cogs.utils")
    await bot.load_extension("cogs.join_logger")

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        await bot.tree.sync(guild=discord.Object(id=EXCLUDED_SERVER_ID))
    except Exception:
        pass



@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    original_embed = None
    is_forwarded_solver = False
    
    if message.author.id == DANK_MEMER_ID:
        if not message.embeds:
            return
        original_embed = message.embeds[0]
    elif message.guild:
        if message.flags.forwarded and message.message_snapshots and message.message_snapshots[0].embeds:
            original_embed = message.message_snapshots[0].embeds[0]
            is_forwarded_solver = True
        elif message.guild.id == EXCLUDED_SERVER_ID and message.embeds:
            original_embed = message.embeds[0]
            is_forwarded_solver = True

    if not original_embed:
        await bot.process_commands(message)
        return

    event_title = original_embed.title
    event_author = original_embed.author.name if original_embed.author else None
    
    event_name = None
    if event_title and event_title in CHANNEL_MAP:
        event_name = event_title
    elif event_author and event_author in CHANNEL_MAP:
        event_name = event_author

    if event_name:
        is_result = False
        is_success = False
        if original_embed.description and not is_forwarded_solver:
            desc_lower = original_embed.description.lower()
            is_result, is_success = _classify_result(desc_lower)

        if is_result and not is_forwarded_solver:
            forwarded_msg = ACTIVE_EVENTS_BY_CHANNEL_TITLE.pop((message.channel.id, event_name), None)
            if forwarded_msg:
                if message.reference and message.reference.message_id in ACTIVE_EVENTS_BY_MSG_ID:
                    ACTIVE_EVENTS_BY_MSG_ID.pop(message.reference.message_id, None)
                
                emoji = "<a:Verified_tick:1501475360791990342>" if is_success else "<a:Wilted_rose:1501475408057733220>"
                for attempt in range(3):
                    try:
                        await forwarded_msg.add_reaction(emoji)
                        break
                    except discord.NotFound:
                        try:
                            forwarded_msg = await forwarded_msg.channel.fetch_message(forwarded_msg.id)
                            await forwarded_msg.add_reaction(emoji)
                            break
                        except Exception:
                            pass
                    except Exception:
                        if attempt < 2:
                            await asyncio.sleep(1)
                    
                if is_success:
                    winner_name = "Someone"
                    winner_mention = None
                    
                    # Extract the winner from interaction, mentions, or the referenced message.
                    inter = getattr(message, 'interaction_metadata', getattr(message, 'interaction', None))
                    if inter and inter.user:
                        winner_name = inter.user.display_name
                        winner_mention = inter.user.mention
                    
                    elif message.mentions:
                        for u in message.mentions:
                            if u.id != DANK_MEMER_ID:
                                winner_name = u.display_name
                                winner_mention = u.mention
                                break
                                
                    if winner_name == "Someone" and message.reference and message.reference.message_id:
                        try:
                            ref_msg = message.reference.cached_message
                            if not ref_msg and hasattr(message.reference, 'resolved') and isinstance(message.reference.resolved, discord.Message):
                                ref_msg = message.reference.resolved
                            
                            if not ref_msg:
                                ref_msg = await message.channel.fetch_message(message.reference.message_id)
                                
                            if ref_msg and ref_msg.author.id != DANK_MEMER_ID:
                                winner_name = ref_msg.author.display_name
                                winner_mention = ref_msg.author.mention
                        except Exception:
                            pass
                    
                    if winner_name == "Someone":
                        for line in (original_embed.description or "").split('\n'):
                            line_lower = line.lower()
                            if " successfully " in line_lower:
                                match = _RE_SUCCESSFULLY.search(line)
                                if match:
                                    winner_name = match.group(1).strip(' *')
                                    break
                            elif " won " in line_lower and " coins" in line_lower:
                                match = _RE_WON.search(line)
                                if match:
                                    winner_name = match.group(1).strip(' *')
                                    break
                            elif " received:" in line_lower:
                                match = _RE_RECEIVED.search(line)
                                if match:
                                    w = match.group(1).strip(' *')
                                    if w.lower() not in ("you", "winner"):
                                        winner_name = w
                                        break

                    content_msg = "Claimed!"
                    if winner_mention:
                        content_msg = f"Claimed by {winner_mention}"
                    elif winner_name != "Someone":
                        content_msg = f"Claimed by **{winner_name}**"

                    success_embed = original_embed.copy()
                    try:
                        await forwarded_msg.channel.send(content=content_msg, embed=success_embed, reference=forwarded_msg)
                    except Exception:
                        pass
            return

        # Remember the image for guessing games.
        if event_name in ("Item Guesser", "Fish Guesser"):
            img_url = None
            if original_embed.image and original_embed.image.url:
                img_url = original_embed.image.url
            elif original_embed.thumbnail and original_embed.thumbnail.url:
                img_url = original_embed.thumbnail.url
            if img_url:
                ext_id = extract_image_id(img_url)
                if ext_id:
                    GUESSER_MEMORY[message.channel.id] = ext_id

        is_excluded = (message.guild and message.guild.id == EXCLUDED_SERVER_ID)
        
        target_channel_id = CHANNEL_MAP[event_name]
        target_channel = bot.get_channel(target_channel_id)
        
        forwarded_msg = None
        
        # Forward the event to the appropriate channel.
        if not is_excluded and target_channel and not is_forwarded_solver:
            invite_url = INVITE_CACHE.get(message.channel.id)
            if not invite_url:
                try:
                    if isinstance(message.channel, discord.Thread):
                        invite = await message.channel.parent.create_invite(max_age=0, max_uses=0)
                    else:
                        invite = await message.channel.create_invite(max_age=0, max_uses=0) 
                    invite_url = invite.url
                    INVITE_CACHE[message.channel.id] = invite_url
                except discord.Forbidden:
                    invite_url = "https://discord.com/ (Bot lacks Create Invite permission!)"
                    INVITE_CACHE[message.channel.id] = invite_url
                except Exception:
                    invite_url = "https://discord.com/ (Error creating invite!)"
                    INVITE_CACHE[message.channel.id] = invite_url

            new_embed = discord.Embed(
                title=event_name,
                description=original_embed.description,
                color=original_embed.color or discord.Color.green()
            )
            
            if original_embed.thumbnail and original_embed.thumbnail.url: 
                new_embed.set_thumbnail(url=original_embed.thumbnail.url)
            if original_embed.image and original_embed.image.url:
                new_embed.set_image(url=original_embed.image.url)
                
            for field in original_embed.fields:
                new_embed.add_field(name=field.name, value=field.value, inline=field.inline)
            
            owner_id = message.guild.owner_id if message.guild else "Unknown"
            server_name = message.guild.name if message.guild else "Unknown Server"
            
            new_embed.add_field(
                name="\u200b",
                value=f"**Server:** {server_name}\n**Owner:** <@{owner_id}>",
                inline=False
            )
            
            new_embed.add_field(
                name="\u200b", 
                value=f"**[Join here]({invite_url})**\n**[Jump to Message]({message.jump_url})**", 
                inline=False
            )
            role_id_to_ping = EVENT_ROLE_MAP.get(event_name, POOKIE_MOD_ROLE_ID)
            forwarded_msg = await target_channel.send(content=f"<@&{role_id_to_ping}>", embed=new_embed)
            
            ACTIVE_EVENTS_BY_MSG_ID[message.id] = forwarded_msg
            ACTIVE_EVENTS_BY_CHANNEL_TITLE[(message.channel.id, event_name)] = forwarded_msg
            
            # Expire the event cache to prevent memory leaks.
            timeout = 630 if event_name in ("Boss Battle", "Dice Champs") else 330
            task = asyncio.create_task(clear_event_cache(message.id, (message.channel.id, event_name), timeout))
            _track_task(task)

        # Attempt to auto-solve the event.
        solver_targets = []
        if is_forwarded_solver:
            solver_targets.append((message.channel, message))
        elif forwarded_msg:
            solver_targets.append((target_channel, forwarded_msg))

        if solver_targets:
            desc_for_solver = original_embed.description or ""
            final_ans = None
            
            if event_name == "Fortnite Dance Mode":
                directions = ARROW_REGEX.findall(desc_for_solver)
                if directions:
                    final_ans = " ".join(d.lower() for d in directions)
                    
            elif event_name == "Reverse Reverse":
                lines = [line for line in desc_for_solver.split('\n') if line.strip()]
                if lines:
                    target_phrase = lines[-1].strip(' *#`')
                    final_ans = target_phrase[::-1]
                    
            elif event_name in ("Item Guesser", "Fish Guesser"):
                target_id = GUESSER_MEMORY.get(message.channel.id)
                if target_id:
                    final_ans = REVERSE_KNOWLEDGE.get(target_id)

            elif event_name == "Dank Scrambled Eggs":
                lines = [line for line in desc_for_solver.split('\n') if line.strip()]
                if lines:
                    scrambled_phrase = lines[-1].strip(' *#`')
                    sorted_scramble = "".join(sorted(scrambled_phrase.lower().replace(" ", "")))
                    if sorted_scramble in ANAGRAM_KNOWLEDGE:
                        final_ans = f"{ANAGRAM_KNOWLEDGE[sorted_scramble]} eggs"
                                    
            else:
                quote_match = SAY_QUOTE_REGEX.search(desc_for_solver)
                if quote_match:
                    final_ans = quote_match.group(1)
            
            if final_ans:
                msg_content = f"``{final_ans}``\n```{final_ans}```"
                for dest_channel, dest_ref in solver_targets:
                    try:
                        await dest_channel.send(msg_content, reference=dest_ref)
                    except Exception:
                        pass

    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    if after.author.id != DANK_MEMER_ID or not after.embeds:
        return

    forwarded_msg = ACTIVE_EVENTS_BY_MSG_ID.get(after.id)
    if not forwarded_msg:
        return

    embed = after.embeds[0]
    desc_lower = embed.description.lower() if embed.description else ""
    
    fields_text = " ".join(
        f"{f.name} {f.value}".lower() for f in embed.fields
    )
    combined_text = f"{desc_lower} {fields_text}"
    
    is_result, is_success = _classify_result(combined_text)

    if is_result:
        forwarded_msg = ACTIVE_EVENTS_BY_MSG_ID.pop(after.id, None)
        
        event_name = embed.title or (embed.author.name if embed.author else None)
        if event_name:
            ACTIVE_EVENTS_BY_CHANNEL_TITLE.pop((after.channel.id, event_name), None)

        if forwarded_msg:
            emoji = "<a:Verified_tick:1501475360791990342>" if is_success else "<a:Wilted_rose:1501475408057733220>"
            for attempt in range(3):
                try:
                    forwarded_msg = await forwarded_msg.channel.fetch_message(forwarded_msg.id)
                    await forwarded_msg.add_reaction(emoji)
                    break
                except discord.NotFound:
                    break
                except Exception:
                    if attempt < 2:
                        await asyncio.sleep(1)

            if is_success and event_name:
                new_embed = embed.copy()
                
                # Preserve our custom server info and link fields.
                if forwarded_msg.embeds:
                    fwd_fields = forwarded_msg.embeds[0].fields
                    if len(fwd_fields) >= 2:
                        for field in fwd_fields[-2:]:
                            new_embed.add_field(name=field.name, value=field.value, inline=field.inline)
                        
                try:
                    await forwarded_msg.edit(embed=new_embed)
                except Exception:
                    pass

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    print(f"Ignoring exception in command {ctx.command}: {error}")

if __name__ == "__main__":
    bot.run(os.getenv('BOT_TOKEN'))
