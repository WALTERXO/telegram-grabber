import asyncio
import pickle
from telethon import TelegramClient, events
from telethon.tl.types import InputMessagesFilterPhotos, MessageMediaPhoto, MessageMediaDocument
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode
from aiogram.utils import executor
import re

api_id = ...
api_hash = '...'
bot_token = '...'

client = TelegramClient('myGrab', api_id, api_hash)
bot = Bot(token=bot_token)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

print("GRAB - Started")

try:
    with open('channels.pickle', 'rb') as f:
        channels = pickle.load(f)
except FileNotFoundError:
    channels = set()
try:
    with open('destination_channels.pickle', 'rb') as f:
        destination_channels = pickle.load(f)
except FileNotFoundError:
    destination_channels = set()
try:
    with open('channel_mapping.pickle', 'rb') as f:
        channel_mapping = pickle.load(f)
except FileNotFoundError:
    channel_mapping = {}

def save_channels():
    with open('channels.pickle', 'wb') as f:
        pickle.dump(channels, f)
    with open('destination_channels.pickle', 'wb') as f:
        pickle.dump(destination_channels, f)
    with open('channel_mapping.pickle', 'wb') as f:
        pickle.dump(channel_mapping, f)


def replace_link(text, new_link):
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    return url_pattern.sub(new_link, text)

def replace_at_word(text, new_word):
    if not text:
        return text
    return re.sub(r'@(\w+)', new_word, text)

new_link = "http://t.me/test"
async def send_media(message, destination_channel_id):
    if message.media and isinstance(message.media, (MessageMediaPhoto, MessageMediaDocument)):
        return await client.send_message(destination_channel_id, message.text, file=message.media)
    else:
        return await client.send_message(destination_channel_id, message.text)
@client.on(events.NewMessage(chats=channels))
async def my_event_handler(event):
    if event.message.grouped_id:
        return

    original_text = event.message.text
    updated_text = replace_link(replace_at_word(original_text, "@test"), new_link)

    for destination_channel_id in destination_channels:
        if event.message.media:
            sent_message = await client.send_file(destination_channel_id, event.message.media, caption=updated_text)
        else:
            sent_message = await client.send_message(destination_channel_id, updated_text)

@client.on(events.Album(chats=channels))
async def album_event_handler(event):
    grouped_media = event.messages
    updated_texts = []
    media_list = []

    for message in grouped_media:
        original_text = message.text
        updated_text = replace_link(replace_at_word(original_text, "@test"), new_link)
        updated_texts.append(updated_text)
        media_list.append(message.media)

    updated_caption = "\n".join([text for text in updated_texts if text])

    for destination_channel_id in destination_channels:
        await client.send_file(destination_channel_id, media_list, caption=updated_caption)

        
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    start_message = (
        "Привет! Я бот для работы с каналами в Telegram. \n\n"
    )
    await message.reply(start_message)

@dp.message_handler(commands=['help'])
async def help(message: types.Message):

    help_message = (
        "Список доступных команд:\n"
        "/start - Начало работы с ботом\n"
        "/help - Получить список доступных команд\n"
        "/add_channel - Добавить канал для работы\n"
        "/remove_channel - Удалить канал из списка\n"
        "/list_channels - Показать список добавленных каналов\n"
        "/add_destination_channel - Добавить канал-получатель\n"
        "/remove_destination_channel - Удалить канал-получатель из списка\n"
        "/list_destination_channels - Показать список каналов-получателей\n"
        "/set_channel_mapping - Установить соответствие между каналами\n"
        "/last_messages (ко-во сообщений или all, если все) - Отправить последние сообщения с каналов\n"
    )

    await message.reply(help_message)

@dp.message_handler(commands=['add_channel'])
async def add_channel(message: types.Message):
    try:
        channel_id = int(message.get_args())
        channels.add(channel_id)
        await message.reply(f"Канал {channel_id} добавлен")
        save_channels()
    except (ValueError, IndexError):
        await message.reply("Пожалуйста, укажите корректный ID канала: /add_channel -1021331290")

@dp.message_handler(commands=['remove_channel'])
async def remove_channel(message: types.Message):
    try:
        channel_id = int(message.get_args())
        channels.discard(channel_id)
        await message.reply(f"Канал {channel_id} удален")
        save_channels()
    except (ValueError, IndexError):
        await message.reply("Пожалуйста, укажите корректный ID канала: /remove_channel -100323213123890")

@dp.message_handler(commands=['list_channels'])
async def list_channels(message: types.Message):
    if channels:
        response = "Список каналов-источников:\n" + "\n".join([f"{channel}" for channel in channels])
    else:
        response = "Список каналов-источников пуст"
    await message.reply(response)

@dp.message_handler(commands=['add_destination_channel'])
async def add_destination_channel(message: types.Message):
    try:
        channel_id = int(message.get_args())
        destination_channels.add(channel_id)
        await message.reply(f"Канал-получатель {channel_id} добавлен")
        save_channels()
    except (ValueError, IndexError):
        await message.reply("Пожалуйста, укажите корректный ID канала-получателя: /add_destination_channel -100321312890")

@dp.message_handler(commands=['remove_destination_channel'])
async def remove_destination_channel(message: types.Message):
    try:
        channel_id = int(message.get_args())
        destination_channels.discard(channel_id)
        await message.reply(f"Канал-получатель {channel_id} удален")
        save_channels()
    except (ValueError, IndexError):
        await message.reply("Пожалуйста, укажите корректный ID канала-получателя: /remove_destination_channel -10013213127890")

@dp.message_handler(commands=['list_destination_channels'])
async def list_destination_channels(message: types.Message):
    if destination_channels:
        response = "Список каналов-получателей:\n" + "\n".join([f"{channel}" for channel in destination_channels])
    else:
        response = "Список каналов-получателей пуст"
    await message.reply(response)

channel_mapping = dict()

@dp.message_handler(commands=['set_channel_mapping'])
async def set_channel_mapping(message: types.Message):
    args = message.get_args().split()
    if len(args) != 2:
        await message.reply("Пожалуйста, укажите ID канала-источника и ID канала-получателя через пробел: /set_channel_mapping -1001234327890 -10003219876324321")
        return

    try:
        source_channel_id = int(args[0])
        destination_channel_id = int(args[1])

        if source_channel_id not in channels:
            await message.reply(f"Канал-источник {source_channel_id} не найден в списке источников")
            return

        if destination_channel_id not in destination_channels:
            await message.reply(f"Канал-получатель {destination_channel_id} не найден в списке получателей")
            return

        channel_mapping[source_channel_id] = destination_channel_id
        await message.reply(f"Канал {source_channel_id} теперь будет пересылать контент на канал {destination_channel_id}")
        save_channels() 

    except (ValueError, IndexError):
        await message.reply("Пожалуйста, укажите корректные ID каналов: /set_channel_mapping -103213890 -100312312321")

@dp.message_handler(commands=['last_messages'])
async def send_last_messages_handler(message: types.Message):
    args = message.get_args().split()
    channel_id = None
    limit = 1

    if len(args) == 2:
        try:
            channel_id = int(args[0])
            if args[1].lower() == "all":
                limit = None
            else:
                limit = int(args[1])
        except ValueError:
            await message.reply("Пожалуйста, укажите корректные ID канала и количество сообщений: /last_messages -1001323290 5 или /last_messages -100321327832190 all")
            return
    elif len(args) == 1:
        try:
            if args[0].lower() == "all":
                limit = None
            else:
                limit = int(args[0])
        except ValueError:
            await message.reply("Пожалуйста, укажите корректное количество сообщений: /last_messages 5 или /last_messages all")
            return

    await send_last_messages(channel_id, limit)
    if limit is None:
        await message.reply("Все сообщения отправлены!")
    else:
        await message.reply(f"{limit} последних сообщений отправлены!")

async def send_last_messages(channel_id=None, limit=None):
    if channel_id is not None:
        if channel_id in channels:
            chat = await client.get_entity(channel_id)
            messages = await client.get_messages(chat, limit=limit)
        else:
            return
    else:
        messages = []
        for channel_id in channels:
            chat = await client.get_entity(channel_id)
            channel_messages = await client.get_messages(chat, limit=limit)
            messages.extend(channel_messages)

    messages = sorted(messages, key=lambda x: x.date)

    grouped_messages = {}
    for message in messages:
        if message.action is None:
            if message.grouped_id:
                if message.grouped_id not in grouped_messages:
                    grouped_messages[message.grouped_id] = [message]
                else:
                    grouped_messages[message.grouped_id].append(message)
            else:
                grouped_messages[message.id] = [message]

    for destination_channel_id in destination_channels:
        for message_group in grouped_messages.values():
            if len(message_group) > 1 and message_group[0].grouped_id:
                media_list = [msg.media for msg in message_group]
                caption = "\n".join([replace_link(replace_at_word(msg.text, "@test"), new_link) for msg in message_group if msg.text])
                await client.send_file(destination_channel_id, media_list, caption=caption)
            else:
                if message_group[0].media:
                    updated_text = replace_link(replace_at_word(message_group[0].text, "@test"), new_link)
                    await client.send_file(destination_channel_id, message_group[0].media, caption=updated_text)
                else:
                    updated_text = replace_link(replace_at_word(message_group[0].text, "@test"), new_link)
                    if updated_text:
                        await client.send_message(destination_channel_id, updated_text)


if __name__ == "__main__":
    async def main():
        await client.start()
        await client.connect()

        dp.register_message_handler(start, commands=['start'], commands_prefix='/')
        dp.register_message_handler(help, commands=['help'], commands_prefix='/')

        await dp.start_polling()
        await client.run_until_disconnected()

    asyncio.run(main())