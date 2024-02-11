from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import logging
import os
import pickle
import re
import sys
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaWebPage, MessageMediaPhoto, MessageMediaDocument
from config import api_id, api_hash, bot_token, my_id, technical_channel_id, new_link, proxy_url, openai_api_key, new_username 
import httpx




# Определение состояния для ожидания ввода ID канала
class ChannelAdding(StatesGroup):
    waiting_for_channel_id = State()

# Установка настроек логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

editing_message_id = None


moderation_active = False
message_storage = {} 

client = TelegramClient('myGrab', api_id, api_hash, system_version="4.16.30-vxMAX")
bot = Bot(token=bot_token)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
logger.info("GRAB - Запущен")

try:
    with open('channels.pickle', 'rb') as f:
        channels = pickle.load(f)
except FileNotFoundError:
    channels = {}

try:
    with open('destination_channels.pickle', 'rb') as f:
        destination_channels = pickle.load(f)
except FileNotFoundError:
    destination_channels = {}

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
    # Ищем ссылки с Markdown форматированием [text](http://url)
    markdown_url_pattern = re.compile(r'\[([^\]]+)\]\(http[s]?://[^\)]+\)')
    # Заменяем URL, сохраняя оригинальный текст ссылки
    return markdown_url_pattern.sub(r'[\1](' + new_link + ')', text)



def replace_at_word(text, new_word):
    if not text:
        return text
    return re.sub(r'@(\w+)', new_word, text)



async def send_media(message, destination_channel_id, allow_forward=True):
    if message.media and isinstance(message.media, (MessageMediaPhoto, MessageMediaDocument)):
        if allow_forward:
            return await client.send_message(destination_channel_id, message.text, file=message.media)
        else:
            downloaded_media = await client.download_media(message.media)
            return await client.send_file(destination_channel_id, downloaded_media, caption=message.text)
    else:
        return await client.send_message(destination_channel_id, message.text)



# Отправка уведомления в Telegram чат
async def send_notification(message):
    chat_id = my_id 
    await bot.send_message(chat_id, message)



bot_id = int(bot_token.split(':')[0])





# Обработка выключения модерации


@dp.callback_query_handler(lambda c: c.data == 'moderation_off')
async def process_moderation_off(callback_query: types.CallbackQuery):
    # Обновите статус модерации
    global moderation_active
    moderation_active = False

    # Отправить уведомление пользователю
    await bot.answer_callback_query(callback_query.id, "Модерация выключена.")




@dp.callback_query_handler(lambda c: c.data.startswith('send_'))
async def process_send(callback_query: types.CallbackQuery):
    message_id = int(callback_query.data.split('_')[1])

    if message_id in message_storage:
        stored_message = message_storage[message_id]

        # Извлечение ID канала из текста сообщения с клавиатуры модерации
        match = re.search(r'ID (-?\d+)', callback_query.message.text)
        if match:
            destination_channel_id = int(match.group(1))
        else:
            # Обработка ошибки: ID канала не найден
            await bot.answer_callback_query(callback_query.id, "Ошибка: ID канала не найден.")
            return

        if isinstance(stored_message, list):  # Обработка альбома
            first_message_caption = stored_message[0].text
            media_group = [message.media for message in stored_message]
            await client.send_file(destination_channel_id, media_group, caption=first_message_caption)

            # Удаление сообщений из технического канала
            message_ids = [msg.id for msg in stored_message]
            await client.delete_messages(technical_channel_id, message_ids)
        else:  # Обработка одиночного сообщения
            # Отправка сообщения на канал с извлеченным ID
            await client.send_message(destination_channel_id, stored_message.text, file=stored_message.media)

            # Удаление сообщения из технического канала
            await client.delete_messages(technical_channel_id, message_id)

        await client.delete_messages(callback_query.message.chat.id, callback_query.message.message_id)
        del message_storage[message_id]
        await bot.answer_callback_query(callback_query.id, "Сообщение(я) отправлено(ы) и удалено(ы).")
    else:
        await bot.answer_callback_query(callback_query.id, "Ошибка: Сообщение не найдено.")















@dp.callback_query_handler(lambda c: c.data.startswith('decline_'))
async def process_decline(callback_query: types.CallbackQuery):
    message_id = int(callback_query.data.split('_')[1])

    if message_id in message_storage:
        try:
            if isinstance(message_storage[message_id], list):  # Если это альбом
                message_ids = [msg.id for msg in message_storage[message_id]]
                await client.delete_messages(technical_channel_id, message_ids)
            else:  # Если это одиночное сообщение
                await client.delete_messages(technical_channel_id, message_id)
            
            del message_storage[message_id]  # Удаление записи из хранилища

            # Дополнительно удаляем модерационное сообщение
            await client.delete_messages(callback_query.message.chat.id, callback_query.message.message_id)

            await bot.answer_callback_query(callback_query.id, "Сообщение отклонено и удалено.")
        except Exception as e:
            await bot.answer_callback_query(callback_query.id, f"Ошибка удаления сообщения: {e}")
    else:
        await bot.answer_callback_query(callback_query.id, "Ошибка: Сообщение не найдено для удаления.")





@dp.callback_query_handler(lambda c: c.data.startswith('edited_'))
async def process_edited(callback_query: types.CallbackQuery):
    message_id = int(callback_query.data.split('_')[1])

    if message_id in message_storage:
        try:
            if isinstance(message_storage[message_id], list):
                # Получаем и обновляем все сообщения в альбоме
                updated_messages = []
                for msg in message_storage[message_id]:
                    edited_message = await client.get_messages(technical_channel_id, ids=msg.id)
                    updated_messages.append(edited_message)
                message_storage[message_id] = updated_messages
            else:
                # Получаем и обновляем одиночное сообщение
                edited_message = await client.get_messages(technical_channel_id, ids=message_id)
                message_storage[message_id] = edited_message

            logger.info(f"Сообщение(я) с ID {message_id} обновлено(ы) в хранилище.")
            await bot.answer_callback_query(callback_query.id, "Сообщение(я) обновлено(ы) в хранилище.")
        except Exception as e:
            logger.error(f"Ошибка при обновлении сообщения с ID {message_id}: {e}")
            await bot.answer_callback_query(callback_query.id, f"Ошибка: {e}")
    else:
        logger.error(f"Сообщение с ID {message_id} не найдено.")
        await bot.answer_callback_query(callback_query.id, "Ошибка: Сообщение не найдено.")






async def get_destination_channel_info(destination_channel_id):
    destination_channel = await client.get_entity(destination_channel_id)
    if destination_channel:
        return destination_channel.title, destination_channel_id
    else:
        return f"Канал с ID {destination_channel_id}", destination_channel_id

@client.on(events.NewMessage(chats=channels))
async def my_event_handler(event):
    if event.message.grouped_id:
        return

    original_text = event.message.text
    updated_text = replace_link(replace_at_word(original_text, new_username), new_link)

    if moderation_active:
        try:
            if event.message.media:
                if isinstance(event.message.media, MessageMediaWebPage):
                    webpage_url = event.message.media.webpage.url
                    updated_text_with_url = f"{updated_text}"
                    sent_message = await client.send_message(technical_channel_id, updated_text_with_url)
                else:
                    sent_message = await client.send_message(technical_channel_id, updated_text, file=event.message.media)

                message_storage[sent_message.id] = sent_message
                moderation_keyboard = InlineKeyboardMarkup(row_width=3).add(
                    InlineKeyboardButton("Отправить", callback_data=f'send_{sent_message.id}'),
                    InlineKeyboardButton("Отклонить", callback_data=f'decline_{sent_message.id}'),
                    InlineKeyboardButton("Отредактировано", callback_data=f'edited_{sent_message.id}'),
                    InlineKeyboardButton("Рерайт текста", callback_data=f'rewrite_{sent_message.id}')
                )
                # Получаем информацию о канале из файла
                destination_channel_id = channel_mapping.get(event.chat_id, None)
                if destination_channel_id is not None:
                    destination_channel_title, _ = await get_destination_channel_info(destination_channel_id)
                    await bot.send_message(technical_channel_id, f"Выберите действие ({destination_channel_title} - ID {destination_channel_id}):", reply_markup=moderation_keyboard)
            else:
                # Обработка случая, когда нет медиа в сообщении
                sent_message = await client.send_message(technical_channel_id, updated_text)
                message_storage[sent_message.id] = sent_message
                moderation_keyboard = InlineKeyboardMarkup(row_width=3).add(
                    InlineKeyboardButton("Отправить", callback_data=f'send_{sent_message.id}'),
                    InlineKeyboardButton("Отклонить", callback_data=f'decline_{sent_message.id}'),
                    InlineKeyboardButton("Отредактировано", callback_data=f'edited_{sent_message.id}'),
                    InlineKeyboardButton("Рерайт текста", callback_data=f'rewrite_{sent_message.id}')
                )
                # Получаем информацию о канале из файла
                destination_channel_id = channel_mapping.get(event.chat_id, None)
                if destination_channel_id is not None:
                    destination_channel_title, _ = await get_destination_channel_info(destination_channel_id)
                    await bot.send_message(technical_channel_id, f"Выберите действие ({destination_channel_title} - ID {destination_channel_id}):", reply_markup=moderation_keyboard)
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {str(e)}")
        return

    for source_channel_id, destination_channel_id in channel_mapping.items():
        if event.chat_id == source_channel_id:
            try:
                if event.message.media:
                    if isinstance(event.message.media, MessageMediaWebPage):
                        webpage_url = event.message.media.webpage.url
                        updated_text_with_url = f"{updated_text}"
                        await client.send_message(destination_channel_id, updated_text_with_url)
                    else:
                        await client.send_file(destination_channel_id, event.message.media, caption=updated_text)
                else:
                    await client.send_message(destination_channel_id, updated_text)

                logger.info(f"Сообщение переслано: {original_text} из канала {source_channel_id} в канал {destination_channel_id}")
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения: {str(e)}")













@client.on(events.Album(chats=channels))
async def album_event_handler(event):
    grouped_media = event.messages
    updated_texts = []
    media_list = []

    for message in grouped_media:
        original_text = message.text
        updated_text = replace_link(replace_at_word(original_text, new_username), new_link)
        updated_texts.append(updated_text)
        media_list.append(message.media)

    updated_caption = "\n".join([text for text in updated_texts if text])

    if moderation_active:
        sent_messages = await client.send_file(technical_channel_id, media_list, caption=updated_caption)
        last_message_id = sent_messages[-1].id

        # Сохраняем весь список сообщений для дальнейшего использования
        message_storage[last_message_id] = sent_messages

        # Получаем информацию о канале из файла
        destination_channel_id = channel_mapping[event.chat_id]
        destination_channel_title, destination_channel_id = await get_destination_channel_info(destination_channel_id)
        

        # Отправка кнопок после сообщения
        moderation_keyboard = InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton("Отправить", callback_data=f'send_{last_message_id}'),
            InlineKeyboardButton("Отклонить", callback_data=f'decline_{last_message_id}'),
            InlineKeyboardButton("Отредактировано", callback_data=f'edited_{last_message_id}')
        )
        await bot.send_message(technical_channel_id, f"Выберите действие ({destination_channel_title} - ID {destination_channel_id}):", reply_markup=moderation_keyboard)
        return

    for source_channel_id, destination_channel_id in channel_mapping.items():
        # Проверяем, что альбом пришел из нужного исходного канала
        if event.chat_id == source_channel_id:
            try:
                await client.send_file(destination_channel_id, media_list, caption=updated_caption)
                logger.info(f"Альбом переслан: {updated_caption}")
            except Exception as e:
                logger.error(f"Ошибка при отправке альбома: {str(e)}")


            






@dp.callback_query_handler(lambda c: c.data.startswith('rewrite_'))
async def process_rewrite(callback_query: types.CallbackQuery):
    message_id = int(callback_query.data.split('_')[1])

    if message_id in message_storage:
        original_message = message_storage[message_id]
        original_text = original_message.text if original_message.text else ""

        rewritten_text = await rewrite_text_with_chatgpt(original_text, openai_api_key)

        await client.edit_message(technical_channel_id, message_id, rewritten_text)
        await bot.answer_callback_query(callback_query.id, "Текст переформулирован.")

proxies = {
    "http://": proxy_url,
    "https://": proxy_url
}




async def rewrite_text_with_chatgpt(text, openai_api_key):
    prompt_text = "Переформулируй этот текст: " + text
    json_data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt_text}]
    }
    headers = {"Authorization": f"Bearer {openai_api_key}"}

    # Установка таймаута для запроса
    timeout = httpx.Timeout(10.0, connect=90.0)

    async with httpx.AsyncClient(proxies=proxies, timeout=timeout) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            json=json_data,
            headers=headers
        )

    if response.status_code == 200:
        response_data = response.json()
        rewritten_text = response_data['choices'][0]['message']['content']
        return rewritten_text
    else:
        print(f"Ошибка запроса: {response.status_code} - {response.text}")
        return None









# Функция для создания клавиатуры с меню
def create_menu_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Помощь", callback_data='help'))
    keyboard.add(InlineKeyboardButton("Добавить канал", callback_data='add_channel'))
    keyboard.add(InlineKeyboardButton("Удалить канал", callback_data='remove_channel'))
    keyboard.add(InlineKeyboardButton("Показать список каналов", callback_data='list_channels'))
    keyboard.add(InlineKeyboardButton("Добавить канал-получатель", callback_data='add_destination_channel'))
    keyboard.add(InlineKeyboardButton("Удалить канал-получатель", callback_data='remove_destination_channel'))
    keyboard.add(InlineKeyboardButton("Показать список каналов-получателей", callback_data='list_destination_channels'))
    keyboard.add(InlineKeyboardButton("Установить соответствие между каналами", callback_data='set_channel_mapping'))
    keyboard.add(InlineKeyboardButton("Показать соответствия", callback_data='show_mapping'))
    keyboard.add(InlineKeyboardButton("Удалить соответствие каналов", callback_data='remove_mapping'))
    keyboard.add(InlineKeyboardButton("Отправить последние сообщения", callback_data='last_messages'))
    keyboard.add(InlineKeyboardButton("Перезагрузить бота", callback_data='restart_bot'))

    # Меняем текст кнопки "Модерация" в зависимости от статуса модерации
    moderation_text = "Модерация: выкл" if moderation_active else "Модерация: вкл"
    keyboard.add(InlineKeyboardButton(moderation_text, callback_data='toggle_moderation'))

    return keyboard




@dp.callback_query_handler(lambda c: c.data == 'show_mapping')
async def process_callback_show_mapping(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    try:
        with open('channel_mapping.pickle', 'rb') as f:
            loaded_mapping = pickle.load(f)

        if loaded_mapping:
            mapping_text = "\n".join(f"{channels[source]} ({source}) -> {destination_channels[destination]} ({destination})"
                                     for source, destination in loaded_mapping.items())
            await bot.send_message(callback_query.from_user.id, "Текущие соответствия каналов:\n" + mapping_text)
        else:
            await bot.send_message(callback_query.from_user.id, "Соответствий каналов пока нет.")
    except FileNotFoundError:
        await bot.send_message(callback_query.from_user.id, "Файл соответствий не найден.")
    except Exception as e:
        await bot.send_message(callback_query.from_user.id, f"Произошла ошибка при загрузке соответствий: {e}")





# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if message.from_user.id != my_id and message.from_user.id != bot_id:
        return 

    start_message = "Привет! Я бот для работы с каналами в Telegram. \n\n Подписывайтесь на наш телеграм канал: https://t.me/my_grab"
    keyboard = create_menu_keyboard()
    await message.reply(start_message, reply_markup=keyboard)


# Обработчик для кнопки "Модерация"
@dp.callback_query_handler(lambda c: c.data == 'toggle_moderation')
async def toggle_moderation(callback_query: types.CallbackQuery):
    global moderation_active
    moderation_active = not moderation_active

    # Отправляем обновленное меню с актуальным статусом модерации
    keyboard = create_menu_keyboard()
    await bot.edit_message_reply_markup(callback_query.message.chat.id, callback_query.message.message_id, reply_markup=keyboard)

    moderation_text = "Модерация включена" if moderation_active else "Модерация выключена"
    await bot.answer_callback_query(callback_query.id, moderation_text)



@dp.callback_query_handler(lambda c: c.data == 'help')
async def process_callback_help(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await help(callback_query.message)





@dp.callback_query_handler(lambda c: c.data == 'add_channel')
async def process_callback_add_channel(callback_query: types.CallbackQuery):
    await ChannelAdding.waiting_for_channel_id.set()
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Введите ID канала или его username, который вы хотите добавить:')
    logger.info("Ожидание ввода ID канала")



@dp.message_handler(state=ChannelAdding.waiting_for_channel_id)
async def add_channel(message: types.Message, state: FSMContext):
    try:
        channel_input = message.text.strip()
        channel_id = None
        chat = None

        # Проверяем, начинается ли введенное значение с "@" (username)
        if channel_input.startswith("@"):
            username = channel_input[1:]  # Убираем символ "@" в начале
            chat = await client.get_entity(username)
        # Проверяем, начинается ли введенное значение с "-" (ID)
        elif channel_input.startswith("-"):
            channel_id = int(channel_input)
            chat = await client.get_entity(channel_id)

        if chat:
            channels[channel_id or chat.id] = chat.title
            await message.reply(f"Канал {chat.title} (ID: {chat.id}) добавлен")
            save_channels()
            logger.info(f"Канал {chat.title} добавлен")
        else:
            await message.reply("Канал не найден. Пожалуйста, укажите корректный ID канала или его username (начинается с '@').")
            logger.error("Ошибка при добавлении канала")
    except Exception as e:
        await message.reply("Произошла ошибка при добавлении канала.")
        logger.error(f"Ошибка при добавлении канала: {str(e)}")
    finally:
        await state.finish()





@dp.callback_query_handler(lambda c: c.data == 'remove_channel')
async def process_callback_remove_channel(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    keyboard = InlineKeyboardMarkup(row_width=1)
    for channel_id, channel_name in channels.items():
        keyboard.insert(InlineKeyboardButton(channel_name, callback_data='remove_channel_' + str(channel_id)))
    await bot.send_message(callback_query.from_user.id, 'Выберите канал, который вы хотите удалить:',
                           reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('remove_channel_'))
async def process_callback_remove_channel_confirm(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    channel_id = int(callback_query.data[len('remove_channel_'):])
    channel_name = channels.pop(channel_id, None)
    if channel_name:
        await bot.send_message(callback_query.from_user.id, f'Канал {channel_name} удален')
        save_channels()
    else:
        await bot.send_message(callback_query.from_user.id, 'Канал не найден')


@dp.callback_query_handler(lambda c: c.data == 'list_channels')
async def process_callback_list_channels(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await list_channels(callback_query.message)


class DestinationChannelAdding(StatesGroup):
    waiting_for_destination_channel_id = State()


@dp.callback_query_handler(lambda c: c.data == 'add_destination_channel')
async def process_callback_add_destination_channel(callback_query: types.CallbackQuery):
    await DestinationChannelAdding.waiting_for_destination_channel_id.set()
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Введите ID канала-получателя или его username, который вы хотите добавить:')



@dp.message_handler(state=DestinationChannelAdding.waiting_for_destination_channel_id)
async def add_destination_channel(message: types.Message, state: FSMContext):
    try:
        channel_input = message.text.strip()
        channel_id = None
        chat = None

        # Проверяем, начинается ли введенное значение с "@" (username)
        if channel_input.startswith("@"):
            username = channel_input[1:]  # Убираем символ "@" в начале
            chat = await client.get_entity(username)
        # Проверяем, начинается ли введенное значение с "-" (ID)
        elif channel_input.startswith("-"):
            channel_id = int(channel_input)
            chat = await client.get_entity(channel_id)

        if chat:
            destination_channels[channel_id or chat.id] = chat.title
            await message.reply(f"Канал-получатель {chat.title} (ID: {chat.id}) добавлен")
            save_channels()
            logger.info(f"Канал-получатель {chat.title} добавлен")
        else:
            await message.reply("Канал-получатель не найден. Пожалуйста, укажите корректный ID канала-получателя или его username (начинается с '@').")
            logger.error("Ошибка при добавлении канала-получателя")
    except Exception as e:
        await message.reply("Произошла ошибка при добавлении канала-получателя.")
        logger.error(f"Ошибка при добавлении канала-получателя: {str(e)}")
    finally:
        await state.finish()





@dp.callback_query_handler(lambda c: c.data == 'remove_destination_channel')
async def process_callback_remove_destination_channel(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    keyboard = InlineKeyboardMarkup(row_width=1)
    for channel_id, channel_name in destination_channels.items():
        keyboard.insert(
            InlineKeyboardButton(channel_name, callback_data='remove_destination_channel_' + str(channel_id)))
    await bot.send_message(callback_query.from_user.id, 'Выберите канал-получатель, который вы хотите удалить:',
                           reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('remove_destination_channel_'))
async def process_callback_remove_destination_channel_confirm(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    channel_id = int(callback_query.data[len('remove_destination_channel_'):])
    channel_name = destination_channels.pop(channel_id, None)
    if channel_name:
        await bot.send_message(callback_query.from_user.id, f'Канал-получатель {channel_name} удален')
        save_channels()
    else:
        await bot.send_message(callback_query.from_user.id, 'Канал-получатель не найден')


@dp.callback_query_handler(lambda c: c.data == 'list_destination_channels')
async def process_callback_list_destination_channels(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await list_destination_channels(callback_query.message)


@dp.callback_query_handler(lambda c: c.data == 'set_channel_mapping')
async def process_callback_set_channel_mapping(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id,
                           'Пожалуйста, введите ID канала-источника и ID канала-получателя через пробел после команды /set_channel_mapping.')
    

@dp.callback_query_handler(lambda c: c.data == 'remove_mapping')
async def process_callback_remove_mapping(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    global channel_mapping
    channel_mapping.clear()  # Очистка всего словаря соответствий
    save_channels()  # Сохранение изменений

    await bot.send_message(callback_query.from_user.id, 'Все соответствия каналов удалены и файл channel_mapping.pickle очищен.')








@dp.callback_query_handler(lambda c: c.data == 'last_messages')
async def process_callback_last_messages(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id,
                           'Пожалуйста, введите количество последних сообщений, которые вы хотите отправить, после команды /last_messages.')


@dp.message_handler(commands=['help'])
async def help(message: types.Message):
    if message.from_user.id != my_id and message.from_user.id != bot_id:
        return  

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
    if message.from_user.id != my_id and message.from_user.id != bot_id:
        return  

    try:
        channel_id = int(message.get_args())
        chat = await client.get_entity(channel_id)
        channels[channel_id] = chat.title
        await message.reply(f"Канал {chat.title} добавлен")
        save_channels()
    except (ValueError, IndexError):
        await message.reply("Пожалуйста, укажите корректный ID канала: /add_channel -1001234567890")



@dp.message_handler(commands=['remove_channel'])
async def remove_channel(message: types.Message):
    if message.from_user.id != my_id and message.from_user.id != bot_id:
        return  

    try:
        channel_id = int(message.get_args())
        if channel_id in channels:
            del channels[channel_id]  # Удаляем, если ключ существует
            await message.reply(f"Канал {channel_id} удален")
            save_channels()
        else:
            await message.reply(f"Канал {channel_id} не найден")
    except (ValueError, IndexError):
        await message.reply("Пожалуйста, укажите корректный ID канала: /remove_channel -1001234567890")




@dp.message_handler(commands=['list_channels'])
async def list_channels(message: types.Message):
    if message.from_user.id != my_id and message.from_user.id != bot_id:
        return  

    if channels:
        await message.reply('\n'.join(f"{name} ({id})" for id, name in channels.items()))
    else:
        await message.reply("Список каналов пуст")



@dp.message_handler(commands=['add_destination_channel'])
async def add_destination_channel(message: types.Message):
    if message.from_user.id != my_id and message.from_user.id != bot_id:
        return 

    try:
        channel_id = int(message.get_args())
        chat = await client.get_entity(channel_id)
        destination_channels[channel_id] = chat.title
        await message.reply(f"Канал-получатель {chat.title} добавлен")
        save_channels()
    except (ValueError, IndexError):
        await message.reply(
            "Пожалуйста, укажите корректный ID канала-получателя: /add_destination_channel -1001234567890")



@dp.message_handler(commands=['remove_destination_channel'])
async def remove_destination_channel(message: types.Message):
    if message.from_user.id != my_id and message.from_user.id != bot_id:
        return 

    try:
        channel_id = int(message.get_args())
        if channel_id in destination_channels:
            del destination_channels[channel_id]  # Удаляем, если ключ существует
            await message.reply(f"Канал-получатель {channel_id} удален")
            save_channels()
        else:
            await message.reply(f"Канал-получатель {channel_id} не найден")
    except (ValueError, IndexError):
        await message.reply(
            "Пожалуйста, укажите корректный ID канала-получателя: /remove_destination_channel -1001234567890")




@dp.message_handler(commands=['list_destination_channels'])
async def list_destination_channels(message: types.Message):
    if message.from_user.id != my_id and message.from_user.id != bot_id:
        return 

    if destination_channels:
        await message.reply('\n'.join(f"{name} ({id})" for id, name in destination_channels.items()))
    else:
        await message.reply("Список каналов-получателей пуст")






@dp.message_handler(commands=['set_channel_mapping'])
async def set_channel_mapping(message: types.Message):
    global channel_mapping

    if message.from_user.id != my_id:
        return  # Игнорировать команду, если ID пользователя не совпадает с my_id

    args = message.get_args().split()
    if len(args) != 2:
        await message.reply(
            "Пожалуйста, укажите ID канала-источника и ID канала-получателя через пробел: /set_channel_mapping -1001234567890 -1000987654321")
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

        # Получение объектов каналов и их названий
        source_channel = await client.get_entity(source_channel_id)
        destination_channel = await client.get_entity(destination_channel_id)

        channel_mapping[source_channel_id] = destination_channel_id
        await message.reply(f"Канал {source_channel.title} ({source_channel_id}) теперь будет пересылать контент на канал {destination_channel.title} ({destination_channel_id})")
        save_channels()
        
        # Обновление соответствий в коде
        try:
            with open('channel_mapping.pickle', 'rb') as f:
                channel_mapping = pickle.load(f)
        except FileNotFoundError:
            channel_mapping = {}

    except (ValueError, IndexError):
        await message.reply(
            "Пожалуйста, укажите корректные ID каналов: /set_channel_mapping -1001234567890 -1000987654321")
    except Exception as e:
        await message.reply(f"Произошла ошибка: {e}")




@dp.message_handler(commands=['last_messages'])
async def send_last_messages_handler(message: types.Message):
    if message.from_user.id != my_id and message.from_user.id != bot_id:
        return 

    args = message.get_args().split()
    source_channel_id = None
    limit = 1

    if len(args) == 2:
        try:
            source_channel_id = int(args[0])
            if args[1].lower() == "all":
                limit = None
            else:
                limit = int(args[1])
        except ValueError:
            await message.reply(
                "Пожалуйста, укажите корректные ID исходного канала и количество сообщений: /last_messages -1001234567890 5 или /last_messages -1001234567890 all")
            return
    elif len(args) == 1:
        try:
            if args[0].lower() == "all":
                limit = None
            else:
                limit = int(args[0])
        except ValueError:
            await message.reply(
                "Пожалуйста, укажите корректное количество сообщений: /last_messages 5 или /last_messages all")
            return

    await send_last_messages(source_channel_id, limit)
    if limit is None:
        await message.reply("Все сообщения отправлены!")
    else:
        await message.reply(f"{limit} последних сообщений отправлены!")

async def send_last_messages(source_channel_id=None, limit=None):
    if source_channel_id is not None:
        destination_channel_id = channel_mapping.get(source_channel_id, None)
        if destination_channel_id is None:
            return
        chat = await client.get_entity(source_channel_id)
        messages = await client.get_messages(chat, limit=limit)
    else:
        messages = []
        for source_channel_id, destination_channel_id in channel_mapping.items():
            chat = await client.get_entity(source_channel_id)
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
                caption = "\n".join([replace_link(replace_at_word(msg.text, new_username), new_link) for msg in message_group if msg.text])
                await client.send_file(destination_channel_id, media_list, caption=caption)
            else:
                for msg in message_group:
                    updated_text = replace_link(replace_at_word(msg.text, new_username), new_link)
                    if msg.media:
                        if isinstance(msg.media, MessageMediaWebPage):
                            # Если есть веб-страница, извлекаем ссылку и отправляем текстовое сообщение
                            webpage_url = msg.media.webpage.url
                            updated_text_with_url = f"{updated_text}"
                            await client.send_message(destination_channel_id, updated_text_with_url)
                        else:
                            # Отправляем файл на целевой канал
                            await client.send_file(destination_channel_id, msg.media, caption=updated_text)
                    else:
                        # Отправляем текстовое сообщение на целевой канал
                        await client.send_message(destination_channel_id, updated_text)




@dp.callback_query_handler(lambda c: c.data == 'restart_bot')
async def process_restart_bot(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await restart_bot(callback_query.message)

async def restart_bot(message: types.Message):
    try:
        await message.reply("Перезагружаю бота... Это может занять несколько секунд.")

        # Остановка бота
        await dp.storage.close()
        await dp.storage.wait_closed()
        
        # Получение и закрытие сессии
        session = await bot.get_session()
        await session.close()

        # Перезапуск скрипта
        os.execl(sys.executable, sys.executable, *sys.argv)

    except Exception as e:
        await message.reply(f"Произошла ошибка при перезагрузке: {e}")




if __name__ == "__main__":
    async def main():
        try:
            # Объявление переменной channel_mapping перед использованием
            global channel_mapping
            channel_mapping = {}

            # Отправка уведомления о запуске бота
            await send_notification("Бот запущен")

            # Обновление соответствий каналов
            try:
                with open('channel_mapping.pickle', 'rb') as f:
                    channel_mapping = pickle.load(f)
            except FileNotFoundError:
                pass

            await client.start()
            await client.connect()

            dp.register_message_handler(start, commands=['start'], commands_prefix='/')
            dp.register_message_handler(help, commands=['help'], commands_prefix='/')

            await dp.start_polling()

        except Exception as e:
            # Отправка уведомления об ошибке
            await send_notification(f"Произошла ошибка: {str(e)}")

        finally:
            # Отправка уведомления об остановке бота
            await send_notification("Бот остановлен")

            await client.disconnect()

    asyncio.run(main())
