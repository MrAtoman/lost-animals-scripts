import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Включение логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Путь к файлу для сохранения данных
DATA_FILE = "annoucements.json"

# ID групп для рассылки
GROUP_LOST = '-1002422080949'  # Замените на ID группы для потерянных животных
GROUP_FOUND = '-1002344810777'  # Замените на ID группы для найденных животных

# Список никнеймов модераторов
MODERATOR_USERNAMES = ['mratoman']  # Замените на никнеймы ваших модераторов

# Загрузка существующих данных из файла
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"last_id": 0, "messages": []}

# Сохранение данных в JSON файл
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Пропало животное", callback_data='lost')],
        [InlineKeyboardButton("Нашли животное", callback_data='found')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите действие:', reply_markup=reply_markup)

# Обработчик кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data in ['lost', 'found']:
        context.user_data['action'] = query.data  # Сохраняем действие
        await query.message.reply_text("Пожалуйста, опишите ситуацию и прикрепите изображение (если есть).")
    else:
        await query.message.reply_text("Неизвестное действие.")

# Обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    action = context.user_data.get('action')
    data = load_data()
    username = update.message.from_user.username
    user_id = update.message.from_user.id
    message_text = update.message.caption if update.message.caption else update.message.text
    image_url = None

    # Получаем ссылку на изображение, если оно есть
    if update.message.photo:
        photo_file = await update.message.photo[-1].get_file()
        image_url = photo_file.file_path

    # Если пользователь отправляет сообщение
    if action:
        last_id = data.get('last_id', 0) + 1
        data['last_id'] = last_id
        
        new_message = {
            "message_id": last_id,
            "user_id": user_id,
            "username": username,
            "message": message_text,
            "image_url": image_url,
            "status": "pending",  # Статус "на модерации"
            "type": action  # Добавляем новый тип сообщения
        }

        # Добавляем новое сообщение в список данных
        data['messages'].append(new_message)
        save_data(data)

        await update.message.reply_text("Ваше сообщение на модерации. Ожидайте одобрения!")
        logger.info(f"Собрано сообщение: {new_message}")

    else:
        await update.message.reply_text("Пожалуйста, сначала выберите действие с помощью команды /start.")

# Обработчик команды /pending для отображения всех сообщений на модерации
async def pending_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.message.from_user.username

    # Проверяем, является ли отправитель модератором
    if username not in MODERATOR_USERNAMES:
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return

    data = load_data()
    pending_msgs = [msg for msg in data['messages'] if msg['status'] == "pending"]

    if not pending_msgs:
        await update.message.reply_text("Нет сообщений на модерации.")
        return

    response = "Сообщения на модерации:\n"
    for msg in pending_msgs:
        response += f"ID: {msg['message_id']}, Сообщение: {msg['message']}\n"

    await update.message.reply_text(response)

# Обработчик команды /approved для одобрения сообщения и отправки его в группу
async def approve_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.message.from_user.username

    # Проверяем, является ли отправитель модератором
    if username not in MODERATOR_USERNAMES:
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Используйте: /approved <ID сообщения>")
        return

    try:
        message_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID сообщения должно быть числом.")
        return

    data = load_data()
    for msg in data['messages']:
        if msg['message_id'] == message_id and msg['status'] == "pending":
            # Обновляем статус сообщения на "approved"
            msg['status'] = 'approved'
            save_data(data)

            # Отправляем сообщение в соответствующую группу
            if msg['type'] == "lost":
                await context.bot.send_message(GROUP_LOST, f"Пропало животное: {msg['message']} {msg['image_url'] if msg['image_url'] else ''}")
                logger.info(f"Сообщение с ID {message_id} отправлено в группу потерянных животных.")
            elif msg['type'] == "found":
                await context.bot.send_message(GROUP_FOUND, f"Нашли животное: {msg['message']} {msg['image_url'] if msg['image_url'] else ''}")
                logger.info(f"Сообщение с ID {message_id} отправлено в группу найденных животных.")

            await update.message.reply_text(f"Сообщение с ID {message_id} одобрено и отправлено в группу.")
            return

    await update.message.reply_text(f"Сообщение с ID {message_id} не найдено или уже одобрено.")

def main():
    token = '7628883106:AAEKohcrXgnecZhvktx4TFcYFeZdM-BfoZg'  # Замените на ваш токен
    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pending", pending_messages))
    application.add_handler(CommandHandler("approved", approve_message))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))

    application.run_polling()

if __name__ == '__main__':
    main()