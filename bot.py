import asyncio
import os
import re

import asyncpg
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

if not TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN environment variable.")

if not DATABASE_URL:
    raise RuntimeError("Missing DATABASE_URL environment variable.")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

channel_state = {}

STAFF_ROLE_ID = 1517204620525699373
DROPPER_ROLE_ID = 1293968356558508195
LOG_CHANNEL_ID = 1518372421306941651

ROBLOX_PER_1M = 20

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

PAYPAL_MESSAGE = (
    "Pay this PayPal (Friends & Family) and send a screenshot afterwards:\n"
    "[PayPal.me/bodygrave](https://www.paypal.com/paypalme/bodygrave)"
)


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


async def create_db_pool():
    return await asyncpg.create_pool(
        dsn=DATABASE_URL,
        min_size=1,
        max_size=5,
        timeout=30,
        command_timeout=30,
    )


async def ensure_tables():
    async with bot.db.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dhc_stats (
                user_id BIGINT PRIMARY KEY,
                dhc INTEGER NOT NULL DEFAULT 0,
                rbx INTEGER NOT NULL DEFAULT 0
            );
            """
        )


async def add_dhc_stat(user_id: int, dhc_amount: int, rbx_amount: int):
    async with bot.db.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO dhc_stats (user_id, dhc, rbx)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id)
            DO UPDATE SET
                dhc = dhc_stats.dhc + EXCLUDED.dhc,
                rbx = dhc_stats.rbx + EXCLUDED.rbx;
            """,
            user_id,
            dhc_amount,
            rbx_amount,
        )


async def get_all_dhc_stats():
    async with bot.db.acquire() as conn:
        return await conn.fetch(
            """
            SELECT user_id, dhc, rbx
            FROM dhc_stats
            WHERE dhc > 0 OR rbx > 0
            ORDER BY dhc DESC, rbx DESC;
            """
        )


@bot.event
async def setup_hook():
    bot.db = await create_db_pool()
    await ensure_tables()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")


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
            "payment": None,
        }

        await asyncio.sleep(1.5)
        await channel.send(
            "How much robux would you like to buy? (FX: 1k, 10k, 100k, 1m)"
        )


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)

    channel = message.channel
    if not isinstance(channel, discord.TextChannel):
        return

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


@bot.command()
async def v(ctx):
    channel = ctx.channel

    if not isinstance(channel, discord.TextChannel):
        return

    if not channel.category or channel.category.name.lower() != "dhc":
        await ctx.send("❌ This command can only be used in DHC tickets.")
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
        f"✅ Order is verified for item: {amount.upper()}!\n\n"
        "What now?\n"
        "Please be patient, your order can take up to a few days.\n"
        "Once a Dropper is available, they will make you join a private server link or ask you to add them on Roblox.\n"
        "After receiving your order, please vouch your dropper."
    )


@bot.command()
async def pp(ctx):
    if not has_role(ctx.author, STAFF_ROLE_ID):
        await ctx.send("❌ You don't have permission to use this command.")
        return

    await ctx.send(
        "[PayPal.me/bodygrave Friends & Family](https://www.paypal.com/paypalme/bodygrave)"
    )


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

    if state.get("finished_by"):
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

    try:
        await add_dhc_stat(ctx.author.id, dhc_amount_number, rbx_price)
    except Exception as e:
        await ctx.send(f"❌ Failed to save DHC stats to database: {e}")
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
        claimed_member = ctx.guild.get_member(claimed_by) if ctx.guild else None
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


@bot.command(name="dhc")
async def dhc_leaderboard(ctx):
    try:
        rows = await get_all_dhc_stats()
    except Exception as e:
        await ctx.send(f"❌ Failed to load leaderboard from database: {e}")
        return

    if not rows:
        await ctx.send("No DHC sales have been logged yet.")
        return

    total_dhc = sum(row["dhc"] for row in rows)
    total_rbx = sum(row["rbx"] for row in rows)

    lines = []
    for index, row in enumerate(rows[:10], start=1):
        user_id = row["user_id"]
        dhc = row["dhc"]
        rbx = row["rbx"]

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
            f"**#{index} {name}** - Dropped: {dhc}m DHC | Earned: {format_number(rbx)} RBX"
        )

    embed = discord.Embed(
        title="Da Hood Cash Leaderboard",
        description="\n".join(lines),
        color=discord.Color.blue()
    )
    embed.add_field(name="Total Dropped", value=f"{total_dhc}m DHC", inline=False)
    embed.add_field(name="Total Earned", value=f"{format_number(total_rbx)} RBX", inline=False)
    embed.add_field(name="Tracked Droppers", value=str(len(rows)), inline=False)
    embed.set_footer(text="Showing top 10 droppers by total DHC dropped")

    await ctx.send(embed=embed)


@bot.event
async def on_disconnect():
    print("Bot disconnected.")


async def main():
    try:
        async with bot:
            await bot.start(TOKEN)
    finally:
        db = getattr(bot, "db", None)
        if db is not None:
            await db.close()


if __name__ == "__main__":
    asyncio.run(main())
