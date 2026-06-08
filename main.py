
from vkbottle.bot import Bot
from dotenv import load_dotenv
import os

load_dotenv()
bot = Bot(os.getenv("VK_TOKEN"))

@bot.on.message(text=["/help","/h"])
async def help_cmd(message):
    await message.answer("Бот запущен")

bot.run()
