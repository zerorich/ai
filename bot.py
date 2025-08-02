import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

# --- Инициализация ---
load_dotenv()
AI_API_KEY = os.getenv("AI_API_KEY")  # API ключ берётся из .env
BOT_TOKEN = os.getenv("BOT_TOKEN")

import google.generativeai as ai
ai.configure(api_key=AI_API_KEY)
_chat_model = ai.GenerativeModel("gemini-1.5-flash")

logging.basicConfig(level=logging.INFO)

def ask_ai(prompt: str) -> str:
    try:
        chat = _chat_model.start_chat(history=[
            {
                "role": "user",
                "parts": [
                    "Ты — умный виртуальный помощник. Не упоминай свою разработку, название модели, компанию Google или любую другую организацию. Отвечай кратко, дружелюбно и понятно."
                ]
            }
        ])
        response = chat.send_message(prompt)
        return response.text
    except Exception as e:
        return "⚠️ Ошибка при ответе."

# --- Обработчики команд ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я умный помощник 🤖. Готов помочь тебе с любыми задачами. Напиши /help, чтобы узнать команды.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
Команды:
/chat <вопрос> — задать вопрос
/summarize <текст> — сократить текст
/code <описание> — сгенерировать код
    """)

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
    prompt = f"Кратко и понятно сожми следующий текст:\n{text}"
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

# --- Запуск ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("chat", chat))
    app.add_handler(CommandHandler("summarize", summarize))
    app.add_handler(CommandHandler("code", code))

    logging.info("🤖 Помощник запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
