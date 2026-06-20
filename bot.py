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


# =========================
# SHIRTS (ALL AMOUNTS)
# =========================
SHIRTS = {
    "1m": "https://www.roblox.com/catalog/17747297153/1-mil",
    "2m": "https://www.roblox.com/catalog/17747298747/2-mil",
    "3m": "https://www.roblox.com/catalog/17747300141/3-mil",
    "4m": "https://www.roblox.com/catalog/17747302120/4-mil",
    "5m": "https://www.roblox.com/catalog/17747303640/5-mil",
    "6m": "https://www.roblox.com/catalog/17747305392/6-mil",
    "7m": "https://www.roblox.com/catalog/17747306563/7-mil",
    "8m": "https://www.roblox.com/catalog/17747307813/8-mil",
    "9m": "https://www.roblox.com/catalog/17747309285/9-mil",
    "10m": "https://www.roblox.com/catalog/17747311491/10-mil",
    "15m": "https://www.roblox.com/catalog/17747312839/15-mil",
    "20m": "https://www.roblox.com/catalog/17747314236/20-mil",
    "25m": "https://www.roblox.com/catalog/17747315326/25-mil",
}


PAYPAL_MESSAGE = (
    "Pay this PayPal (Friends & Family) and send a screenshot afterwards:\n"
    "https://www.paypal.com/paypalme/bodygrave"
)


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
    elif cat == "Dhc":

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

                # 🔥 ONLY CHANGE: buying vs selling behavior
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

    if not any(role.id == STAFF_ROLE_ID for role in ctx.author.roles):
        await ctx.send("❌ You don't have permission to use this command.")
        return

    amount = None

    for key in SHIRTS.keys():
        if key in channel.name.lower():
            amount = key
            break

    if not amount and channel.id in channel_state:
        amount = channel_state[channel.id].get("amount")

    if not amount:
        amount = "unknown"

    await channel.edit(name=f"{amount}-paid")

    await channel.send(
        f"✅ Order is verified for item: {amount}!\n\n"
        "What now?\n"
        "Please be patient, your order can take up to a few days\n"
        "Once a Dropper is available, they will make you join a private server link or ask you to add them on Roblox.\n"
        "After receiving your order, please vouch your dropper."
    )


bot.run(TOKEN)
