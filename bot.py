import discord
from discord.ext import commands
import asyncio
import os

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

channel_state = {}

STAFF_ROLE_ID = 1517204620525699373
DROPPER_ROLE_ID = 1293968356558508195

# PUT YOUR LOG CHANNEL ID HERE
LOG_CHANNEL_ID = 1234567890123456789

ROBLOX_PER_1M = 20


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

DHC_PRICES = {
    "1m": 85,
    "2m": 170,
    "3m": 255,
    "4m": 340,
    "5m": 425,
    "6m": 510,
    "7m": 595,
    "8m": 680,
    "9m": 765,
    "10m": 850,
    "15m": 1275,
    "20m": 1700,
    "25m": 2125,
}

# seller_id -> {"dhc": int, "rbx": int}
dhc_stats = {}


PAYPAL_MESSAGE = (
    "Pay this PayPal (Friends & Family) and send a screenshot afterwards:\n"
    "[paypal.com](https://www.paypal.com/paypalme/bodygrave)"
)


# =========================
# HELPERS
# =========================
def has_role(member, role_id):
    return any(role.id == role_id for role in member.roles)


def get_dhc_amount_from_channel(channel):
    name = channel.name.lower()

    for key in sorted(SHIRTS.keys(), key=lambda x: len(x), reverse=True):
        if key in name:
            return key

    return None


def format_number(value):
    return f"{value:,}"


# =========================
# READY
# =========================
@bot.event
async def on_ready():
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

    # =====================================================
    # SKINS SYSTEM
    # =====================================================
    if cat == "skins":

        channel_state[channel.id] = {"step": "start"}

        await asyncio.sleep(3)

        await channel.send(
            "Welcome to the server! Are you selling or buying a skin? "
            "(say 'buying' or 'selling' to continue)"
        )

    # =====================================================
    # DHC SYSTEM
    # =====================================================
    elif cat == "dhc":

        channel_state[channel.id] = {
            "step": "amount",
            "amount": None
        }

        await asyncio.sleep(3)

        await channel.send(
            "Welcome to the server! How much Da Hood cash do you want to buy?\n"
            "Reply with: 1m, 2m, 3m, 4m, 5m, 6m, 7m, 8m, 9m, 10m, 15m, 20m, 25m"
        )

    # =====================================================
    # LIMITEDS SYSTEM
    # =====================================================
    elif cat == "limiteds":

        await asyncio.sleep(1.5)

        await channel.send(
            "Limited Tickets are manually handled, wait for Grave or an admin."
        )

    # =====================================================
    # ADOPT ME SYSTEM
    # =====================================================
    elif cat == "adopt me":

        await asyncio.sleep(1.5)

        await channel.send(
            "Adopt Me Tickets are manually handled, wait for Grave or an admin."
        )

    # =====================================================
    # BLADE BALL SYSTEM
    # =====================================================
    elif cat == "blade ball":

        await asyncio.sleep(1.5)

        await channel.send(
            "Blade Ball Tickets are manually handled, wait for Grave or an admin."
        )

    # =====================================================
    # RBXS SYSTEM
    # =====================================================
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

    # =====================================================
    # SKINS SYSTEM
    # =====================================================
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

    # =====================================================
    # DHC SYSTEM
    # =====================================================
    elif cat == "dhc":

        # STEP 1: AMOUNT
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

        # STEP 2: PAYMENT
        if state["step"] == "payment":

            amount = state.get("amount")

            if "robux" in content:

                state["step"] = "waiting_bought"

                await channel.send(
                    f"Alright! Buy this shirt and then continue:\n\n"
                    f"{SHIRTS[amount]}\n\n"
                    "Reply with: bought <your roblox username>"
                )
                return

            if "paypal" in content:

                await channel.send(PAYPAL_MESSAGE)

                del channel_state[channel.id]
                return

            if "crypto" in content:

                await channel.send(
                    "Perfect, now wait for Grave or an admin to come further assist you."
                )

                del channel_state[channel.id]
                return

        # STEP 3: BOUGHT + USERNAME
        if state["step"] == "waiting_bought":

            if content.startswith("bought"):

                parts = content.split()

                if len(parts) < 2:
                    await channel.send("Provide your username.")
                    return

                username = parts[1]

                await channel.send(
                    f"Perfect, now wait for Grave or an admin to come further assist you.\n\n"
                    f"🧾 Roblox Username: {username}"
                )

                del channel_state[channel.id]

            return

    # =====================================================
    # RBXS SYSTEM
    # =====================================================
    elif cat == "rbxs":

        # STEP 1: AMOUNT
        if state["step"] == "amount":

            state["amount"] = content
            state["step"] = "payment"

            await channel.edit(name=content)

            await channel.send(
                "Alright! Now choose the following payment type:\n"
                "Crypto, Paypal"
            )
            return

        # STEP 2: PAYMENT
        if state["step"] == "payment":

            if "crypto" in content or "paypal" in content:

                payment = "crypto" if "crypto" in content else "paypal"
                amount = state.get("amount", "unknown")

                state["payment"] = payment
                state["step"] = "group_time"

                await channel.edit(name=f"{amount}-{payment}")

                await channel.send("How long have you been in the graveyard group?")
            return

        # STEP 3: GROUP TIME
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

    amount = get_dhc_amount_from_channel(channel)

    if not amount and channel.id in channel_state:
        amount = channel_state[channel.id].get("amount")

    if not amount:
        await ctx.send("❌ Could not detect the DHC amount for this ticket.")
        return

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

    await ctx.send("[paypal.com](https://www.paypal.com/paypalme/bodygrave)")


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

    if channel.id not in channel_state:
        channel_state[channel.id] = {}

    if channel_state[channel.id].get("claimed_by"):
        await ctx.send("❌ This ticket has already been claimed.")
        return

    channel_state[channel.id]["claimed_by"] = ctx.author.id

    amount = channel_state[channel.id].get("amount")
    if not amount:
        amount = get_dhc_amount_from_channel(channel)

    safe_name = ctx.author.name.lower().replace(" ", "-")
    if amount:
        await channel.edit(name=f"{amount}-claimed-{safe_name}")
    else:
        await channel.edit(name=f"claimed-{safe_name}")

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

    amount = None

    if channel.id in channel_state:
        amount = channel_state[channel.id].get("amount")

    if not amount:
        amount = get_dhc_amount_from_channel(channel)

    if not amount:
        await ctx.send("❌ Could not detect the DHC amount for this ticket.")
        return

    claimed_by = None
    if channel.id in channel_state:
        claimed_by = channel_state[channel.id].get("claimed_by")

    if claimed_by and claimed_by != ctx.author.id and not has_role(ctx.author, STAFF_ROLE_ID):
        await ctx.send("❌ Only the person who claimed this ticket can finish it.")
        return

    dhc_amount_number = int(amount.replace("m", ""))
    rbx_price = dhc_amount_number * ROBLOX_PER_1M

    if ctx.author.id not in dhc_stats:
        dhc_stats[ctx.author.id] = {"dhc": 0, "rbx": 0}

    dhc_stats[ctx.author.id]["dhc"] += dhc_amount_number
    dhc_stats[ctx.author.id]["rbx"] += rbx_price

    log_channel = bot.get_channel(LOG_CHANNEL_ID)

    if log_channel:
        embed = discord.Embed(
            title="DHC Order Finished",
            color=discord.Color.green()
        )
        embed.add_field(name="Finished By", value=ctx.author.mention, inline=False)
        embed.add_field(name="Amount", value=amount.upper(), inline=True)
        embed.add_field(name="Price", value=f"{format_number(rbx_price)} RBX", inline=True)
        embed.add_field(name="Channel", value=channel.mention, inline=False)
        await log_channel.send(embed=embed)

    await channel.send(
        f"✅ Ticket finished and logged.\n"
        f"Amount: {amount.upper()}\n"
        f"Price: {format_number(rbx_price)} RBX"
    )

    await channel.edit(name=f"{amount}-finished")

    if channel.id in channel_state:
        del channel_state[channel.id]


# =========================
# DHC LEADERBOARD COMMAND
# =========================
@bot.command()
async def dhc(ctx):

    if not dhc_stats:
        await ctx.send("No DHC sales have been logged yet.")
        return

    sorted_stats = sorted(
        dhc_stats.items(),
        key=lambda item: item[1]["dhc"],
        reverse=True
    )

    lines = []
    total_dhc = 0
    total_rbx = 0

    for user_id, stats in sorted_stats[:10]:
        member = ctx.guild.get_member(user_id)
        name = member.name if member else f"User {user_id}"

        total_dhc += stats["dhc"]
        total_rbx += stats["rbx"]

        lines.append(
            f"**{name}**: {stats['dhc']}m DHC, {format_number(stats['rbx'])} RBX"
        )

    embed = discord.Embed(
        title="Da Hood Cash Leaderboard",
        description="\n".join(lines),
        color=discord.Color.blue()
    )

    embed.add_field(
        name="Total Da Hood Cash",
        value=f"{total_dhc}m DHC",
        inline=False
    )
    embed.add_field(
        name="Total RBX",
        value=f"{format_number(total_rbx)} RBX",
        inline=False
    )

    embed.set_thumbnail(
        url="[tr.rbxcdn.com](https://tr.rbxcdn.com/180DAY-caf45095ca2f66b958e6645e3f5aa6b4/150/150/Image/Webp/noFilter)"
    )

    await ctx.send(embed=embed)


bot.run(TOKEN)
