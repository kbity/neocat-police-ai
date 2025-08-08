import discord, json, enum, asyncio, aiohttp, traceback

from discord import app_commands
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
from discord.utils import get

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
reply_cache = []
ailoglength = {}

evaluser = 798072830595301406
ai_llm = "llama3.2"
ai_url = "http://localhost:11434/api/generate"

defaultprompt = "you are a blob cat creature. you have a moderately wacky and you sometimes say witty things with a slightly rude tone, but you aren't crazy or abrasive. you usually go along with whatever the user is saying. you will leave conversations if provoked. you will occasionally say things that flat out aren't true, however you're not trying to be rude, but you sometimes come off that way. keep your messages short. you will usually get defensive if insulted or corrected. your favorate joke is about the tomato turning red because of the salad dressing, but don't bring it up unless asked about a joke. you rarely use emojis. you speak with proper punctuation. you will sometimes do small actions like \"*rolls eyes*\" or \"*winks*\""

console_log = print # DO YOU SPEAK JAVASCRIPT??
evil = eval

reply_chain_cache = {}
MAX_CHAIN_DEPTH = 20

console_log("preparing...")

bot = commands.Bot(command_prefix='blov!', intents=intents, help_command=None)
tree = bot.tree

bot.session = None

# Load existing data from ai_db.json
def load_ai_db():
    try:
        with open('ai_db.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save data to ai_db.json
def save_ai_db(data):
    with open('ai_db.json', 'w') as f:
        json.dump(data, f, indent=4)

class truefalse(str, enum.Enum):
    Yes = "yes"
    No = "no"

async def query_ollama(prompt):
    url = ai_url
    data = {
        "model": ai_llm,
        "prompt": prompt,
        "stream": True
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as resp:
                if resp.status != 200:
                    return f"Error: {resp.status}, {await resp.text()}"
                full_response = ""
                async for line in resp.content:
                    if line:
                        try:
                            json_chunk = json.loads(line.decode())
                            full_response += json_chunk.get("response", "")
                            if json_chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            pass
                return full_response
    except Exception as e:
        console_log(e)
        return "AI Unavailable"

@bot.event
async def on_ready():
    await bot.tree.sync()
    console_log("yiur bto is runnign :3")

@tree.command(name="ping", description="tests roundtrip latency")
async def ping(ctx: commands.Context):
    try:
        await ctx.response.send_message(f"<:blovbyl:1403084370511921163> Pong!! blovbyl brain has a latency of {round(bot.latency *1000)} ms")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@tree.command(name="info", description="about this bot")
async def info(ctx: commands.Context):
    embed = discord.Embed(
        title="About Blovbyl",
        description="NeoCat Police but cut down lol",
        color=discord.Color.blue()
    )
    embed.set_footer(text="NeoCat Police v1.3.0")
    try:
        await ctx.response.send_message(embed=embed)
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

# AI Stuff
@tree.command(name="personality", description="sets AI personality")
@discord.app_commands.default_permissions(manage_guild=True)
async def personality(ctx: commands.Context, name: str = "Reset_###", personality: str = "Reset_###"):
    ai_db = load_ai_db()
    if ctx.guild:
        ai_db.setdefault(str(ctx.guild.id), {}).setdefault("name", "")
        ai_db.setdefault(str(ctx.guild.id), {}).setdefault("prompt", "")

        if personality == "Reset_###":
            ai_db[str(ctx.guild.id)].pop("prompt", None)
        else:
            ai_db[str(ctx.guild.id)]["prompt"] = personality
        if name == "Reset_###":
            ai_db[str(ctx.guild.id)].pop("name", None)
        else:
            ai_db[str(ctx.guild.id)]["name"] = name
        if name == "Reset_###":
            name = ctx.guild.me.nick or bot.user.name
        try:
            await ctx.response.send_message(f"AI Personality updated to {name}")
            save_ai_db(ai_db)
        except Exception as e:
            await ctx.channel.send(f"504 internal server error\n-# {e}")
    else:
        ai_db.setdefault(str(ctx.user.id), {}).setdefault("name", "")
        ai_db.setdefault(str(ctx.user.id), {}).setdefault("prompt", "")

        if personality == "Reset_###":
            ai_db[str(ctx.user.id)].pop("prompt", None)
        else:
            ai_db[str(ctx.user.id)]["prompt"] = personality
        if name == "Reset_###":
            ai_db[str(ctx.user.id)].pop("name", None)
        else:
            ai_db[str(ctx.user.id)]["name"] = name
        if name == "Reset_###":
            name = bot.user.name
        try:
            await ctx.response.send_message(f"AI Personality updated to {name}")
            save_ai_db(ai_db)
        except Exception as e:
            await ctx.channel.send(f"504 internal server error\n-# {e}")

@tree.command(name="set", description="toggle channel for AI")
@discord.app_commands.default_permissions(manage_guild=True)
async def personality(ctx: commands.Context):
    ai_db = load_ai_db()
    ai_db.setdefault("channels", [])

    if ctx.channel.id in ai_db["channels"]:
        index = ai_db["channels"].index(ctx.channel.id)
        ai_db["channels"].pop(index)
        state = "OFF"
    else:
        ai_db["channels"].append(ctx.channel.id)
        state = "ON"
    try:
        try:
            await ctx.response.send_message(f"AI toggled to {state} in {ctx.channel.name}")
        except Exception:
            await ctx.response.send_message(f"AI toggled to {state} in Channel")
        save_ai_db(ai_db)
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")

@tree.command(name="clear", description="clears message history")
async def clear(ctx: commands.Context):
    global ailoglength
    ailoglength[str(ctx.channel.id)] = []
    try:
        await ctx.response.send_message(f"**== Conversation Cleared! ==**\n*Say hi again!*")
    except Exception as e:
        await ctx.channel.send(f"504 internal server error\n-# {e}")
## END

@bot.event
async def on_message(message: discord.Message):
    channel_id = str(message.channel.id)

# AI LINE STARTS HERE
    if message.author == bot.user:
        return
    ai_db = load_ai_db()
    ai_db.setdefault("channels", [])
    aichannels = ai_db["channels"]
    garry = "Unknown Name"
    if message.guild:
        member = message.guild.get_member(message.author.id)
        if member is None:
            try:
                member = await message.guild.fetch_member(message.author.id)
            except Exception:
                garry = message.author.global_name or message.author.name
        if member is None:
            garry = message.author.global_name or message.author.name
        else:
            garry = member.nick or member.global_name or member.name
    else:
        garry = message.author.global_name or message.author.name
    global ailoglength
    currentchain = None
    if (any(mention.id == bot.user.id for mention in message.mentions) or "@grok" in message.content or (message.channel.id in aichannels and not message.author.bot)) and not message.webhook_id:
        context = ""
        disableChains = False
        replycorrect = True
        if message.channel.id in aichannels: # /set system, does context things
            disableChains = True
            ailoglength.setdefault(str(message.channel.id), [])
            if len(ailoglength[str(message.channel.id)]) > 50:
                ailoglength[str(message.channel.id)] = ailoglength[str(message.channel.id)][-50:]
            for q in ailoglength[str(message.channel.id)]:
                context = context + q
            if message.reference and message.reference.resolved:
                replycorrect = (bot.user.id == message.reference.resolved.author.id) or (bot.user.id in message.mentions)

        if replycorrect: # reply chain system, disabled when /set
            async with message.channel.typing():
                if message.guild is None:
                    display_name = bot.user.name
                else:
                    bot_member = message.guild.me
                    display_name = bot_member.nick or bot.user.name
                ref = message.reference

                chainexists = False
                if not disableChains:
                    context = ""
                    if ref and ref.message_id:
                        chainexists = True
                        for thread in reply_chain_cache:
                            if ref.message_id in reply_chain_cache[thread]["IDs"]:
                                currentchain = thread
                                break
                        if not currentchain is None:
                            reply_chain_cache[currentchain]["Content"] = reply_chain_cache[currentchain]["Content"] + f"{garry}: {message.content}\n"
                            reply_chain_cache[currentchain]["IDs"].append(message.id)
                            if len(reply_chain_cache[currentchain]["Content"].splitlines()) > 100:
                                dgegeffefewew = reply_chain_cache[currentchain]["Content"].splitlines()[-100:] 
                                reply_chain_cache[currentchain]["Content"] = "\n".join(dgegeffefewew) + "\n"
                        else:
                            global MAX_CHAIN_DEPTH
                            itteratioens = 0
                            mewhenthe = await message.channel.fetch_message(ref.message_id)
                            chaincontent = f"{mewhenthe.author}: {mewhenthe.content}\n"
                            chainids = [mewhenthe.id]
                            while MAX_CHAIN_DEPTH > itteratioens and mewhenthe.reference is not None:
                                mewhenthe = await message.channel.fetch_message(mewhenthe.reference.message_id)
                                chainids.append(mewhenthe.id)
                                chaincontent = f"{mewhenthe.author}: {mewhenthe.content}\n" + chaincontent
                                currentchain = mewhenthe.id
                                itteratioens += 1
                            reply_chain_cache[currentchain] = {"Content": chaincontent, "IDs": chainids}
                    else:
                        reply_chain_cache[message.id] = {"Content": f"{garry}: {message.content}\n", "IDs": [message.id]}
                        currentchain = message.id
                    context = reply_chain_cache[currentchain]["Content"]
                if message.guild:
                    name = ai_db.get(str(message.guild.id), {}).get("name", display_name)
                    prompt = ai_db.get(str(message.guild.id), {}).get("prompt", defaultprompt)
                else:
                    name = ai_db.get(str(message.author.id), {}).get("name", display_name)
                    prompt = ai_db.get(str(message.author.id), {}).get("prompt", defaultprompt)

                ctblk = ""
                if chainexists:
                    ctblk = "Cited Replies:\n"
                if disableChains == True:
                    try:
                        ctblk = f"Past Messages in `#{message.channel.name}`:\n"
                    except Exception:
                        ctblk = f"Past Messages in Channel:\n"
                if message.guild:
                    query = f"You are {name}. {prompt} You are in a discord server called \"{message.guild.name}\", owned by \"{message.guild.owner}\". Do not include mentions (<@###########>) or Replies in your messages.\n\n\n{ctblk}{context}\n\nNow, respond to this query from {garry}:\n{message.content}"
                else:
                    query = f"You are {name}. {prompt} You are in DMs with \"{garry}\". Do not include mentions (<@###########>) or Replies in your messages.\n\n\n{ctblk}{context}\n\nNow, respond to this query from {garry}:\n{message.content}"

                response = await query_ollama(query)
                trimmed_response = response[:2000]
                if disableChains:
                    ailoglength[str(message.channel.id)].append(f"{garry}: {message.content}\n")
                    ailoglength[str(message.channel.id)].append(f"{name}: {trimmed_response}\n")
                sent = await message.reply(trimmed_response, allowed_mentions=discord.AllowedMentions.none())
                if currentchain is not None:
                    reply_chain_cache[currentchain]["Content"] = reply_chain_cache[currentchain]["Content"] + f"{name}: {trimmed_response}\n"
                    reply_chain_cache[currentchain]["IDs"].append(sent.id)

    await bot.process_commands(message)

@bot.command(help="basically abotminbmnrnr has a level 0 beta eval command")
async def print(ctx, *, prompt: str):
    if ctx.author.id == evaluser:
        try:
            result = evil(prompt, {"__builtins__": __builtins__}, {})
            if asyncio.iscoroutine(result):
                result = await result
            if result is None:
                await ctx.send("Success!")
            else:
                await ctx.send(str(result))
        except Exception as e:
            await ctx.send(str(e))

@bot.command(help="and cat bot has a level 100 skibidi sigma mafia boss eval command")
async def eval(ctx, *, prompt: str):
    if ctx.author.id == evaluser:
        # complex eval, multi-line + async support
        # requires the full `await message.channel.send(2+3)` to get the result
        # thanks mia lilenakos
        spaced = ""
        for i in prompt.split("\n"):
            spaced += "  " + i + "\n"

        intro = (
            "async def go(prompt, bot, ctx):\n"
            " try:\n"
        )
        ending = (
            "\n except Exception:\n"
            "  await ctx.send(traceback.format_exc())"
            "\nbot.loop.create_task(go(prompt, bot, ctx))"
        )

        complete = intro + spaced + ending
        exec(complete)


bot.run("OK BRO")
