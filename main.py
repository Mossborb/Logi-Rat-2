import discord
from discord.ext import commands
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
import asyncio
import os

load_dotenv()
BOT_TOKEN = os.getenv('DISCORD_TOKEN')



active_timers = []

# Required for the bot to read messages
intents = discord.Intents.default()
intents.message_content = True

# Create bot instance with command prefix
bot = commands.Bot(command_prefix="!", intents=intents)



# Event: when bot is ready
@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")
    await update_status()

async def update_status():
    if len(active_timers) == 0:
        await bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="for new orders 👀")
        )
    else:
        await bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name=f"processing {len(active_timers)} order(s) 🔧")
        )


@bot.command()
async def MPFTimer(ctx, *args):
    try:
        if "@" not in args:
            await ctx.send("❌ Use `@` to separate the item name from the time. Example: `!MPFTimer 9x Ammo @ 01:00`")
            return

        at_index = args.index("@")

        if at_index < 2 or at_index == len(args) - 1:
            await ctx.send("❌ Invalid format. Example: `!MPFTimer 9x Ammo @ 01:00`")
            return

        # Get amount, strip 'x'
        amount_str = args[0].lower().replace("x", "")
        if not amount_str.isdigit():
            await ctx.send("❌ Invalid crate amount. Use a number like `9x` or `9`.")
            return
        amount = int(amount_str)

        # Item name = everything between amount and @
        item = " ".join(args[1:at_index])

        # Time = everything after @
        cook_time = " ".join(args[at_index + 1:])

        # Parse time
        time_parts = cook_time.split(":")
        if len(time_parts) == 2:
            hours, minutes = map(int, time_parts)
            delta = timedelta(hours=hours, minutes=minutes)
        elif len(time_parts) == 3:
            days, hours, minutes = map(int, time_parts)
            delta = timedelta(days=days, hours=hours, minutes=minutes)
        else:
            await ctx.send("❌ Time must be in HH:MM or DD:HH:MM format.")
            return

        # Calculate ready time
        ready_time = datetime.utcnow() + delta  # UTC for timestamp
        unix_ts = int(ready_time.timestamp())

        await ctx.send(f"🛠️ {amount} crates of {item} will be ready <t:{unix_ts}:t> (<t:{unix_ts}:R>).")

        # Save to active_timers
        active_timers.append({
            "user": ctx.author.mention,
            "amount": amount,
            "item": item,
            "ready_time": ready_time,
        })
        await update_status()

        await asyncio.sleep(delta.total_seconds())

        # Remove after it's ready
        active_timers[:] = [t for t in active_timers if t["ready_time"] != ready_time or t["user"] != ctx.author.mention]
        await update_status()

        role = discord.utils.get(ctx.guild.roles, name="Logistic") #This is archived
        role_mention = role.mention if role else "@Logistic" #This is archived 
        await ctx.send(f"✅ {ctx.author.mention}, {amount} crates of {item} are ready! <t:{unix_ts}:t>")

    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")


@bot.command()
async def MPFTimerList(ctx):
    if not active_timers:
        await ctx.send("📭 No active MPF timers. GO GET COOKIN!")
        return

    now = datetime.utcnow()
    lines = []

    for t in active_timers:
        remaining = t["ready_time"] - now
        if remaining.total_seconds() <= 0:
            continue

        unix_ts = int(t["ready_time"].timestamp())
        lines.append(
            f"🧱 {t['amount']}x {t['item']} — {t['user']} — Ready <t:{unix_ts}:t> (<t:{unix_ts}:R>)"
        )

    if not lines:
        await ctx.send("📭 No active MPF timers.")
    else:
        await ctx.send("📋 **Active MPF Timers:**\n" + "\n".join(lines))

bot.run(BOT_TOKEN)
