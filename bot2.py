from telebot.async_telebot import AsyncTeleBot
import asyncio
from chat_gpt import get_responce

bot = AsyncTeleBot('')

@bot.message_handler(commands=['start', '/start'])
async def start_reaction(message):
        await bot.send_message(chat_id=message.chat.id, text="""
        Укажите в произвольном порядке следующие особенности недвижимости (обязательно указать все):

        Вторичное/нет 
        Ближайшая станция метро
        Минут до станции метро
        Регион 
        Количество комнат 
        Площадь 
        Этаж 
        Сколько этажей в доме всего 
        Опишите ремонт
        """)

@bot.message_handler(func=lambda message: True)
async def message_handler(message):
    await bot.send_message(chat_id=message.chat.id, text=get_responce(message.text))

if __name__ == '__main__':
    a = asyncio.get_event_loop()
    a.create_task(bot.polling())
    a.run_forever()
