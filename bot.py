import os
import logging
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
import google.generativeai as genai

# --- Настройки ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
AI_API_KEY = os.getenv("AI_API_KEY")

genai.configure(api_key=AI_API_KEY)
_model = genai.GenerativeModel("gemini-1.5-flash")

logging.basicConfig(level=logging.INFO)

# --- Общая функция запроса к ИИ ---
def ask_ai(prompt: str, image: Image.Image = None) -> str:
    try:
        if image:
            # Правильный способ передачи изображения в Gemini
            response = _model.generate_content([prompt, image])
        else:
            response = _model.generate_content(prompt)
        
        return response.text
    except Exception as e:
        logging.error(f"Ошибка AI: {e}")
        return "⚠️ Не удалось получить ответ от ИИ."

# --- Команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💬 Задать вопрос", callback_data="chat")],
        [InlineKeyboardButton("📝 Сжать текст", callback_data="summarize")],
        [InlineKeyboardButton("👨‍💻 Генерация кода", callback_data="code")],
        [InlineKeyboardButton("📈 Торговый сигнал", callback_data="trade")],
    ]
    await update.message.reply_text(
        "Привет! Я умный помощник 🤖. Что хочешь сделать?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
Команды:
/chat <вопрос> — задать вопрос
/summarize <текст> — сжать текст
/code <описание> — сгенерировать код
/trade — отправь фото графика, и я дам торговый сигнал
""")

# --- Инлайн-обработка ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    command = query.data

    if command == "chat":
        await query.message.reply_text("Напиши: /chat <твой вопрос>")
    elif command == "summarize":
        await query.message.reply_text("Напиши: /summarize <текст>")
    elif command == "code":
        await query.message.reply_text("Напиши: /code <описание кода>")
    elif command == "trade":
        await query.message.reply_text("Отправь изображение графика (например, XAUUSD), и я дам торговый сигнал.")

# --- Обработка фото для торговли ---
async def handle_trade_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Получаем фото наибольшего размера
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        
        # Загружаем изображение как BytesIO
        image_bytes = BytesIO()
        await photo_file.download_to_memory(image_bytes)
        image_bytes.seek(0)
        
        # Открываем изображение с помощью PIL
        image = Image.open(image_bytes)
        
        # Конвертируем в RGB если необходимо
        if image.mode != 'RGB':
            image = image.convert('RGB')

        prompt = (
            "На изображении график трейдинга (например, XAUUSD). "
            "Проанализируй его и определи: BUY или SELL, точку входа, "
            "рекомендуемый Take Profit и Stop Loss. Формат:\n\n"
            "Сигнал: BUY или SELL\n"
            "Вход: <уровень>\nTP: <уровень>\nSL: <уровень>\n\n"
            "Кратко и точно, без упоминания, что ты ИИ."
        )

        response = ask_ai(prompt, image)
        await update.message.reply_text(response)
        
    except Exception as e:
        logging.error(f"Ошибка обработки изображения: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка при обработке изображения. Попробуйте еще раз.")

# --- Другие команды ---
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Напиши вопрос после /chat.")
        return
    prompt = " ".join(context.args)
    reply = ask_ai(prompt)
    await update.message.reply_text(reply)

async def summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Напиши текст для сжатия.")
        return
    text = " ".join(context.args)
    prompt = f"Сожми и перефразируй кратко:\n{text}"
    reply = ask_ai(prompt)
    await update.message.reply_text(reply)

async def code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Опиши, какой код нужен.")
        return
    task = " ".join(context.args)
    prompt = f"Напиши код по описанию:\n{task}"
    reply = ask_ai(prompt)
    await update.message.reply_text(reply)

# --- Запуск бота ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("chat", chat))
    app.add_handler(CommandHandler("summarize", summarize))
    app.add_handler(CommandHandler("code", code))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_trade_photo))

    logging.info("🤖 Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()