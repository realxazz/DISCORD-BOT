import discord
from discord.ext import commands
import asyncio
import os
import re
import json

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

channel_state = {}

STAFF_ROLE_ID = 1517204620525699373
DROPPER_ROLE_ID = 1293968356558508195

# PUT YOUR REAL LOG CHANNEL ID HERE
LOG_CHANNEL_ID = 1518372421306941651

ROBLOX_PER_1M = 20
STATS_FILE = "dhc_stats.json"


# =========================
# SHIRTS (ALL AMOUNTS)
# =========================
SHIRTS = {
    "1m": "[1 Million DHC Shirt](https://www.roblox.com/catalog/17747297153/1-mil)",
    "2m": "[2 Million DHC Shirt](https://www.roblox.com/catalog/17747298747/2-mil)",
    "3m": "[3 Million DHC Shirt](https://www.roblox.com/catalog/17747300141/3-mil)",
    "4m": "[4 Million DHC Shirt](https://www.roblox.com/catalog/17747302120/4-mil)",
    "5m": "[5 Million DHC Shirt](https://www.roblox.com/catalog/17747303640/5-mil)",
    "6m": "[6 Million DHC Shirt](https://www.roblox.com/catalog/17747305392/6-mil)",
    "7m": "[7 Million DHC Shirt](https://www.roblox.com/catalog/17747306563/7-mil)",
    "8m": "[8 Million DHC Shirt](https://www.roblox.com/catalog/17747307813/8-mil)",
    "9m": "[9 Million DHC Shirt](https://www.roblox.com/catalog/17747309285/9-mil)",
    "10m": "[10 Million DHC Shirt](https://www.roblox.com/catalog/17747311491/10-mil)",
    "15m": "[15 Million DHC Shirt](https://www.roblox.com/catalog/17747312839/15-mil)",
    "20m": "[20 Million DHC Shirt](https://www.roblox.com/catalog/17747314236/20-mil)",
    "25m": "[25 Million DHC Shirt](https://www.roblox.com/catalog/17747315326/25-mil)",
}

# user_id -> {"dhc": int, "rbx": int}
dhc_stats = {}

PAYPAL_MESSAGE = (
    "Pay this PayPal (Friends & Family) and send a screenshot afterwards:\n"
    "[PayPal.Me/bodygrave](https://www.paypal.com/paypalme/bodygrave)"
)


# =========================
# HELPERS
# =========================
def has_role(member, role_id):
    return any(role.id == role_id for role in member.roles)


def format_number(value):
    return f"{value:,}"


def get_dhc_amount_from_text(text):
    text = text.lower()
    valid_amounts = set(SHIRTS.keys())

    for amount in sorted(valid_amounts, key=lambda x: len(x), reverse=True):
        if amount in text:
            return amount

    match = re.search(r"\b(\d{1,2})m\b", text)
    if match:
        possible_amount = f"{match.group(1)}m"
        if possible_amount in valid_amounts:
            return possible_amount

    return None


def get_dhc_amount_from_channel(channel):
    return get_dhc_amount_from_text(channel.name)


def get_or_create_ticket_state(channel_id):
    if channel_id not in channel_state:
        channel_state[channel_id] = {
            "step": None,
            "amount": None,
            "claimed_by": None,
            "finished_by": None,
        }
    return channel_state[channel_id]


def parse_dhc_millions(amount):
    return int(amount.replace("m", ""))


def load_stats():
    global dhc_statsou s

    if not os.path.exists(STATS_FILE):
        dhc_stats = {}
        return

    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        dhc_stats = {}
        for user_id, stats in data.items():
            dhc_stats[int(user_id)] = {
                "dhc": int(stats.get("dhc", 0)),
                "rbx": int(stats.get("rbx", 0)),
            }
    except Exception as e:
        print(f"Failed to load stats: {e}")
        dhc_stats = {}


def save_stats():
    try:
        serializable = {str(user_id): stats for user_id, stats in dhc_stats.items()}
        temp_file = f"{STATS_FILE}.tmp"

        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=4)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_file, STATS_FILE)
        return True
    except Exception as e:
        print(f"Failed to save stats: {e}")
        return False


# =========================
# READY
# =========================
@bot.event
async def on_ready():
    load_stats()
    print(f"Logged in as {bot.user}")


# =========================
# CHANNEL CREATE
# =========================
@bot.event
async def on_guild_channel_create(channel):

    if not isinstance(channel, discord.TextChannel):
        return

    if not channel.category:
        return

    cat = channel.category.name.lower()

    if cat == "skins":
        channel_state[channel.id] = {"step": "start"}

        await asyncio.sleep(3)
        await channel.send(
            "Welcome to the server! Are you selling or buying a skin? "
            "(say 'buying' or 'selling' to continue)"
        )

    elif cat == "dhc":
        channel_state[channel.id] = {
            "step": "amount",
            "amount": None,
            "claimed_by": None,
            "finished_by": None,
        }

        await asyncio.sleep(3)
        await channel.send(
            "Welcome to the server! How much Da Hood cash do you want to buy?\n"
            "Reply with: 1m, 2m, 3m, 4m, 5m, 6m, 7m, 8m, 9m, 10m, 15m, 20m, 25m"
        )

    elif cat == "limiteds":
        await asyncio.sleep(1.5)
        await channel.send(
            "Limited Tickets are manually handled, wait for Grave or an admin."
        )

    elif cat == "adopt me":
        await asyncio.sleep(1.5)
        await channel.send(
            "Adopt Me Tickets are manually handled, wait for Grave or an admin."
        )

    elif cat == "blade ball":
        await asyncio.sleep(1.5)
        await channel.send(
            "Blade Ball Tickets are manually handled, wait for Grave or an admin."
        )

    elif cat == "rbxs":
        channel_state[channel.id] = {
            "step": "amount",
            "amount": None,
            "payment": None
        }

        await asyncio.sleep(1.5)
        await channel.send(
            "How much robux would you like to buy? (FX: 1k, 10k, 100k, 1m)"
        )


# =========================
# MESSAGE HANDLER
# =========================
@bot.event
async def on_message(message):

    if message.author.bot:
        return

    channel = message.channel

    await bot.process_commands(message)

    if channel.id not in channel_state:
        return

    state = channel_state[channel.id]
    content = message.content.lower().strip()

    cat = channel.category.name.lower() if channel.category else ""

    if cat == "skins":

        if state["step"] == "start":

            if "selling" in content:
                state["type"] = "selling"
                state["step"] = "waiting_item"
                await channel.send("Alright! What skin are you Selling?")

            elif "buying" in content:
                state["type"] = "buying"
                state["step"] = "waiting_item"
                await channel.send("Alright! What skin are you Buying?")

            return

        if state["step"] == "waiting_item":
            state["step"] = "payment"
            await channel.send(
                "Alright perfect, what payment method would you prefer for this? "
                "(say 'crypto' or 'paypal' to continue)"
            )
            return

        if state["step"] == "payment":

            if "paypal" in content:
                payment = "paypal"
                trade_type = state.get("type", "unknown")

                await channel.edit(name=f"{trade_type}-{payment}")

                if trade_type == "buying":
                    await channel.send(PAYPAL_MESSAGE)
                else:
                    await channel.send(
                        "Perfect, now wait for Grave or an admin to come further assist you."
                    )

                del channel_state[channel.id]
                return

            if "crypto" in content:
                payment = "crypto"
                trade_type = state.get("type", "unknown")

                await channel.edit(name=f"{trade_type}-{payment}")

                await channel.send(
                    "Perfect, now wait for Grave or an admin to come further assist you."
                )

                del channel_state[channel.id]
                return

    elif cat == "dhc":

        if state["step"] == "amount":

            if content in SHIRTS:
                state["amount"] = content
                state["step"] = "payment"

                await channel.edit(name=content)

                await channel.send(
                    "Alright! Now choose the following payment type:\n"
                    "Robux, Crypto, Paypal"
                )

            return

        if state["step"] == "payment":
            amount = state.get("amount")

            if "robux" in content and amount in SHIRTS:
                state["step"] = "waiting_bought"

                await channel.send(
                    f"Alright! Buy this shirt and then continue:\n\n"
                    f"{SHIRTS[amount]}\n\n"
                    "Reply with: bought <your roblox username>"
                )
                return

            if "paypal" in content:
                await channel.send(PAYPAL_MESSAGE)
                return

            if "crypto" in content:
                await channel.send(
                    "Perfect, now wait for Grave or an admin to come further assist you."
                )
                return

        if state["step"] == "waiting_bought":

            if content.startswith("bought"):
                parts = content.split(maxsplit=1)

                if len(parts) < 2:
                    await channel.send("Provide your username.")
                    return

                username = parts[1].strip()

                await channel.send(
                    f"Perfect, now wait for Grave or an admin to come further assist you.\n\n"
                    f"🧾 Roblox Username: {username}"
                )

                state["step"] = "done"
                return

    elif cat == "rbxs":

        if state["step"] == "amount":
            state["amount"] = content
            state["step"] = "payment"

            await channel.edit(name=content)

            await channel.send(
                "Alright! Now choose the following payment type:\n"
                "Crypto, Paypal"
            )
            return

        if state["step"] == "payment":

            if "crypto" in content or "paypal" in content:
                payment = "crypto" if "crypto" in content else "paypal"
                amount = state.get("amount", "unknown")

                state["payment"] = payment
                state["step"] = "group_time"

                await channel.edit(name=f"{amount}-{payment}")

                await channel.send("How long have you been in the graveyard group?")
            return

        if state["step"] == "group_time":
            await channel.send(
                "Perfect, now wait for Grave or an admin to come further assist you."
            )

            del channel_state[channel.id]
            return


# =========================
# STAFF VERIFY COMMAND
# =========================
@bot.command()
async def v(ctx):

    channel = ctx.channel

    if not isinstance(channel, discord.TextChannel):
        return

    if not channel.category or channel.category.name.lower() != "dhc":
        return

    if not has_role(ctx.author, STAFF_ROLE_ID):
        await ctx.send("❌ You don't have permission to use this command.")
        return

    state = get_or_create_ticket_state(channel.id)

    amount = state.get("amount")
    if not amount:
        amount = get_dhc_amount_from_channel(channel)

    if not amount:
        await ctx.send("❌ Could not detect the DHC amount for this ticket.")
        return

    if state.get("finished_by") or state.get("step") == "finished":
        await ctx.send("❌ This ticket has already been finished.")
        return

    state["amount"] = amount
    state["step"] = "verified"

    await channel.edit(name=f"{amount}-paid")

    await channel.send(
        f"✅ Order is verified for item: {amount}!\n\n"
        "What now?\n"
        "Please be patient, your order can take up to a few days\n"
        "Once a Dropper is available, they will make you join a private server link or ask you to add them on Roblox.\n"
        "After receiving your order, please vouch your dropper."
    )


# =========================
# STAFF PAYPAL COMMAND
# =========================
@bot.command()
async def pp(ctx):

    if not has_role(ctx.author, STAFF_ROLE_ID):
        await ctx.send("❌ You don't have permission to use this command.")
        return

    await ctx.send("[Pay with Friends & Family PayPal.me/bodygrave](https://www.paypal.com/paypalme/bodygrave)")


# =========================
# CLAIM COMMAND
# =========================
@bot.command()
async def claim(ctx):

    channel = ctx.channel

    if not isinstance(channel, discord.TextChannel):
        return

    if not has_role(ctx.author, DROPPER_ROLE_ID):
        await ctx.send("❌ You don't have permission to use this command.")
        return

    if not channel.category or channel.category.name.lower() != "dhc":
        await ctx.send("❌ This command can only be used in DHC tickets.")
        return

    state = get_or_create_ticket_state(channel.id)

    finished_by = state.get("finished_by")
    if finished_by:
        await ctx.send("❌ This ticket has already been finished.")
        return

    amount = state.get("amount")
    if not amount:
        amount = get_dhc_amount_from_channel(channel)

    if not amount:
        await ctx.send("❌ Could not detect the DHC amount for this ticket.")
        return

    existing_claimed_by = state.get("claimed_by")
    if existing_claimed_by and existing_claimed_by != ctx.author.id:
        await ctx.send("❌ This ticket has already been claimed.")
        return

    state["amount"] = amount
    state["claimed_by"] = ctx.author.id

    await ctx.send(f"✅ {ctx.author.mention} has claimed this ticket.")


# =========================
# FINISHED COMMAND
# =========================
@bot.command()
async def finished(ctx):

    channel = ctx.channel

    if not isinstance(channel, discord.TextChannel):
        return

    if not has_role(ctx.author, DROPPER_ROLE_ID):
        await ctx.send("❌ You don't have permission to use this command.")
        return

    if not channel.category or channel.category.name.lower() != "dhc":
        await ctx.send("❌ This command can only be used in DHC tickets.")
        return

    state = get_or_create_ticket_state(channel.id)

    amount = state.get("amount")
    if not amount:
        amount = get_dhc_amount_from_channel(channel)

    if not amount:
        await ctx.send("❌ Could not detect the DHC amount for this ticket.")
        return

    state["amount"] = amount

    claimed_by = state.get("claimed_by")
    finished_by = state.get("finished_by")

    if finished_by:
        await ctx.send("❌ This ticket has already been finished.")
        return

    if claimed_by and claimed_by != ctx.author.id and not has_role(ctx.author, STAFF_ROLE_ID):
        await ctx.send("❌ Only the person who claimed this ticket can finish it.")
        return

    dhc_amount_number = parse_dhc_millions(amount)
    rbx_price = dhc_amount_number * ROBLOX_PER_1M

    if ctx.author.id not in dhc_stats:
        dhc_stats[ctx.author.id] = {"dhc": 0, "rbx": 0}

    dhc_stats[ctx.author.id]["dhc"] += dhc_amount_number
    dhc_stats[ctx.author.id]["rbx"] += rbx_price

    if not save_stats():
        await ctx.send("❌ Failed to save DHC stats. The ticket was not safely recorded.")
        return

    state["finished_by"] = ctx.author.id
    state["step"] = "finished"

    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel is None:
        try:
            log_channel = await bot.fetch_channel(LOG_CHANNEL_ID)
        except Exception:
            log_channel = None

    claimed_member = None
    if claimed_by:
        claimed_member = ctx.guild.get_member(claimed_by)
        if claimed_member is None:
            try:
                claimed_member = await bot.fetch_user(claimed_by)
            except Exception:
                claimed_member = None

    if log_channel:
        embed = discord.Embed(
            title="DHC Order Finished",
            color=discord.Color.green()
        )
        embed.add_field(name="Finished By", value=ctx.author.mention, inline=False)
        embed.add_field(
            name="Claimed By",
            value=claimed_member.mention if claimed_member else "Not claimed",
            inline=False
        )
        embed.add_field(name="Amount", value=amount.upper(), inline=True)
        embed.add_field(name="Price", value=f"{format_number(rbx_price)} RBX", inline=True)
        embed.add_field(name="Channel", value=channel.mention, inline=False)

        try:
            await log_channel.send(embed=embed)
        except Exception as e:
            await ctx.send(f"⚠️ Could not send log message: {e}")
    else:
        await ctx.send("⚠️ Log channel not found. Check LOG_CHANNEL_ID.")

    await channel.send(
        f"✅ Ticket finished and logged.\n"
        f"Amount: {amount.upper()}\n"
        f"Price: {format_number(rbx_price)} RBX"
    )

    await channel.edit(name=f"{amount}-finished")


# =========================
# DHC LEADERBOARD COMMAND
# =========================
@bot.command(name="dhc")
async def dhc_leaderboard(ctx):

    load_stats()

    valid_stats = {
        user_id: stats
        for user_id, stats in dhc_stats.items()
        if isinstance(stats, dict)
        and isinstance(stats.get("dhc"), int)
        and isinstance(stats.get("rbx"), int)
        and (stats.get("dhc", 0) > 0 or stats.get("rbx", 0) > 0)
    }

    if not valid_stats:
        await ctx.send("No DHC sales have been logged yet.")
        return

    sorted_stats = sorted(
        valid_stats.items(),
        key=lambda item: item[1]["dhc"],
        reverse=True
    )

    total_dhc = sum(stats["dhc"] for stats in valid_stats.values())
    total_rbx = sum(stats["rbx"] for stats in valid_stats.values())

    lines = []
    for index, (user_id, stats) in enumerate(sorted_stats[:10], start=1):
        member = ctx.guild.get_member(user_id) if ctx.guild else None

        if member:
            name = member.display_name
        else:
            try:
                user = await bot.fetch_user(user_id)
                name = user.name
            except Exception:
                name = f"User {user_id}"

        lines.append(
            f"**#{index} {name}** - Dropped: {stats['dhc']}m DHC | Earned: {format_number(stats['rbx'])} RBX"
        )

    embed = discord.Embed(
        title="Da Hood Cash Leaderboard",
        description="\n".join(lines),
        color=discord.Color.blue()
    )

    embed.add_field(
        name="Total Dropped",
        value=f"{total_dhc}m DHC",
        inline=False
    )
    embed.add_field(
        name="Total Earned",
        value=f"{format_number(total_rbx)} RBX",
        inline=False
    )
    embed.add_field(
        name="Tracked Droppers",
        value=str(len(valid_stats)),
        inline=False
    )

    embed.set_footer(text="Showing top 10 droppers by total DHC dropped")

    await ctx.send(embed=embed)


bot.run(TOKEN)
