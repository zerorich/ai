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
def clean_markdown(text: str) -> str:
    """Удаляет markdown разметку из текста"""
    import re
    # Убираем жирный текст **text**
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    # Убираем курсив *text*
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    # Убираем подчеркивание _text_
    text = re.sub(r'_(.*?)_', r'\1', text)
    # Убираем зачеркнутый текст ~~text~~
    text = re.sub(r'~~(.*?)~~', r'\1', text)
    return text

def ask_ai(prompt: str, image: Image.Image = None) -> str:
    try:
        if image:
            # Правильный способ передачи изображения в Gemini
            response = _model.generate_content([prompt, image])
        else:
            response = _model.generate_content(prompt)
        
        # Очищаем ответ от markdown разметки
        clean_response = clean_markdown(response.text)
        return clean_response
    except Exception as e:
        logging.error(f"Ошибка AI: {e}")
        return "⚠️ Не удалось получить ответ от ИИ."

# --- Команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💬 Задать вопрос", callback_data="chat")],
        [InlineKeyboardButton("📝 Сжать текст", callback_data="summarize")],
        [InlineKeyboardButton("👨‍💻 Генерация кода", callback_data="code")],
        [InlineKeyboardButton("📈 Быстрый сигнал", callback_data="trade")],
        [InlineKeyboardButton("🔍 Детальный анализ", callback_data="detailed")],
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
/trade — отправь фото графика для быстрого сигнала
/analysis — отправь фото для детального анализа
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
        context.user_data['analysis_type'] = 'quick'
        await query.message.reply_text("Отправь изображение графика для быстрого торгового сигнала.")
    elif command == "detailed":
        context.user_data['analysis_type'] = 'detailed'
        await query.message.reply_text("Отправь изображение графика для детального технического анализа.")

# --- Другие команды ---
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

        # Проверяем тип анализа
        analysis_type = context.user_data.get('analysis_type', 'quick')
        
        if analysis_type == 'detailed':
            prompt = (
                "Сделай профессиональный технический анализ этого графика:\n\n"
                "📈 ТЕХНИЧЕСКИЙ АНАЛИЗ:\n"
                "• Текущая цена: [читай точно с графика]\n"
                "• Тренд: [краткосрочный и долгосрочный]\n"
                "• Паттерн свечей: [что показывают последние свечи]\n"
                "• Уровни поддержки: [конкретные цены]\n"
                "• Уровни сопротивления: [конкретные цены]\n"
                "• Объемы: [если видны на графике]\n\n"
                "🎯 ТОРГОВЫЕ ВОЗМОЖНОСТИ:\n"
                "1. ПОКУПКА:\n"
                "   - Вход от уровня: [цена]\n"
                "   - TP1: [цена] | TP2: [цена]\n"
                "   - SL: [цена]\n"
                "   - Риск/Прибыль: [соотношение]\n\n"
                "2. ПРОДАЖА:\n"
                "   - Вход от уровня: [цена]\n"
                "   - TP1: [цена] | TP2: [цена]\n"
                "   - SL: [цена]\n"
                "   - Риск/Прибыль: [соотношение]\n\n"
                "⚡ РЕКОМЕНДАЦИЯ:\n"
                "[Лучший сценарий на основе анализа]\n\n"
                "ВАЖНО: НЕ используй звездочки или markdown разметку в ответе! "
                "Используй только простой текст с эмодзи. "
                "Читай цены с графика максимально точно, не угадывай!"
            )
        else:
            prompt = (
                "Проанализируй этот торговый график детально:\n\n"
                "1. Определи текущую цену и тренд\n"
                "2. Найди ключевые уровни поддержки и сопротивления\n"
                "3. Проанализируй паттерны свечей и объем\n"
                "4. Учти трендовые линии и технические индикаторы\n"
                "5. Оцени риск/прибыль соотношение\n\n"
                "НА ОСНОВЕ ТОЧНОГО АНАЛИЗА дай торговый сигнал:\n\n"
                "📊 АНАЛИЗ:\n"
                "Текущая цена: [точная цена с графика]\n"
                "Тренд: [восходящий/нисходящий/боковой]\n"
                "Ключевые уровни: [укажи конкретные уровни]\n\n"
                "🎯 ТОРГОВЫЙ СИГНАЛ:\n"
                "Направление: BUY/SELL\n"
                "Вход: [точная цена входа]\n"
                "Take Profit: [обоснованный TP]\n"
                "Stop Loss: [обоснованный SL]\n"
                "Risk/Reward: [соотношение]\n\n"
                "💡 ОБОСНОВАНИЕ:\n"
                "[Объясни почему именно такой сигнал]\n\n"
                "ВАЖНО: НЕ используй звездочки, markdown или специальные символы! "
                "Отвечай простым текстом с эмодзи. "
                "Читай цены с графика максимально точно!"
            )

        response = ask_ai(prompt, image)
        await update.message.reply_text(response)
        
        # Сбрасываем тип анализа
        context.user_data.pop('analysis_type', None)
        
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