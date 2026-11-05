import os
import discord
from discord.ext import commands
import openai
from flask import Flask
from threading import Thread

# Flask server 24/7 active байлгах
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Discord Intents тохируулах
intents = discord.Intents.default()
intents.message_content = True  # Message content intent шаардлагатай
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

# OpenAI client тохиргоо
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')

# System prompt: Латин болон кирилл монгол хэлийг ялгаж ойлгох, хариулах заавар
SYSTEM_PROMPT = (
    "You are a helpful Discord AI assistant. "
    "If the user writes in Mongolian using Latin script (latin mongol), "
    "you should reply in Latin script as well. "
    "If they write in Cyrillic, reply in Cyrillic."
)

# 1. !ai команчаар ажиллах хэсэг
@bot.command(name='ai')
async def ask_ai(ctx, *, prompt: str):
    async with ctx.typing():
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )
            answer = response.choices[0].message.content
            await ctx.send(answer)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

# 2. Ботыг шууд меншн (@BotName) хийж асуух хэсэг
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Хэрэв ботыг меншн хийсэн бол
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        prompt = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()
        
        if prompt:
            async with message.channel.typing():
                try:
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=500
                    )
                    answer = response.choices[0].message.content
                    await message.reply(answer)
                except Exception as e:
                    await message.reply(f"An error occurred: {e}")

    # Бусад командууд ажиллахын тулд зайлшгүй шаардлагатай
    await bot.process_commands(message)

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.environ.get("DISCORD_TOKEN")
    bot.run(TOKEN)