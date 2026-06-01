import os
import threading
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from barber_db import add_appointment, get_all_appointments, get_working_hours, add_working_hour

# --- ХАК ДЛЯ БЕЗКОШТОВНОГО RENDER ---
class HealthCheckServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is running safely and for free!")
    def log_message(self, format, *args):
        return

def start_health_server():
    port = int(os.environ.get("PORT", 8080))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckServer)
        server.serve_forever()
    except Exception as e:
        print(f"❌ Помилка мікро-сервера: {e}", flush=True)
# -------------------------------------

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ BOT_TOKEN не знайдено!", flush=True)
    sys.exit(1)

ADMIN_ID = 1717915313 

# --- ФУНКЦІЇ БОТА ---

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id == ADMIN_ID:
        keyboard = [
            [InlineKeyboardButton("➕ Додати вільний час", callback_data="admin_add_time")],
            [InlineKeyboardButton("📋 Подивитися всі записи", callback_data="admin_view_appointments")]
        ]
        await update.message.reply_text("👑 Панель Адміністратора:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("❌ Відмовлено в доступі.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("✂️ Записатися", callback_data="start_booking")]]
    await update.message.reply_text("Вітаємо в Барбершопі 'NINJA'! 🥷", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # --- КЛІЄНТСЬКА ЧАСТИНА ---
    if data == "start_booking":
        keyboard = [
            [InlineKeyboardButton("💇‍♂️ Чоловіча стрижка", callback_data="srv_Стрижка")],
            [InlineKeyboardButton("🧔 Моделювання бороди", callback_data="srv_Борода")]
        ]
        await query.edit_message_text("Оберіть послугу:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("srv_"):
        context.user_data['service'] = data.split("_")[1]
        
        # Динамічно беремо вільний час із бази даних!
        available_times = get_working_hours()
        keyboard = []
        
        # Будуємо кнопки по 2 в ряд
        for i in range(0, len(available_times), 2):
            row = [InlineKeyboardButton(f"🕙 {available_times[i]}", callback_data=f"time_{available_times[i]}")]
            if i + 1 < len(available_times):
                row.append(InlineKeyboardButton(f"🕙 {available_times[i+1]}", callback_data=f"time_{available_times[i+1]}"))
            keyboard.append(row)
            
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="start_booking")])
        await query.edit_message_text("Оберіть зручний час:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("time_"):
        time = data.split("_")[1]
        service = context.user_data.get('service', 'Стрижка')
        username = query.from_user.username or query.from_user.first_name
        
        add_appointment(query.from_user.id, username, service, time)
        await query.edit_message_text(f"✅ Успішно записано!\n\nКлієнт: @{username}\nПослуга: {service}\nЧас: {time}")

    # --- АДМІНСЬКА ЧАСТИНА ---
    elif data == "back_to_admin":
        keyboard = [
            [InlineKeyboardButton("➕ Додати вільний час", callback_data="admin_add_time")],
            [InlineKeyboardButton("📋 Подивитися всі записи", callback_data="admin_view_appointments")]
        ]
        await query.edit_message_text("👑 Панель Адміністратора:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "admin_add_time":
        # Ставимо мітку у сесію адміна, що ми чекаємо від нього текст із часом
        context.user_data['awaiting_time_input'] = True
        keyboard = [[InlineKeyboardButton("🔙 Скасувати", callback_data="back_to_admin")]]
        await query.edit_message_text(
            "⏳ Напишіть у чат час, який хочете додати (наприклад: `19:00` чи `20:30`):", 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    elif data == "admin_view_appointments":
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_admin")]]
        try:
            records = get_all_appointments()
            if not records:
                report = "📋 Наразі немає записів."
            else:
                report = "📋 Актуальні записи:\n\n"
                for row in records:
                    report += f"⏰ {row[2]} — @{row[0]} ({row[1]})\n"
        except Exception as e:
            report = f"❌ Помилка БД: {e}"
        await query.edit_message_text(report, reply_markup=InlineKeyboardMarkup(keyboard))

# Функція обробки текстових повідомлень (для введення часу адміном)
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # Перевіряємо, чи це пише адмін і чи бот взагалі чекає від нього введення часу
    if user_id == ADMIN_ID and context.user_data.get('awaiting_time_input'):
        new_time = update.message.text.strip()
        
        # Скидаємо прапорець очікування
        context.user_data['awaiting_time_input'] = False
        
        success = add_working_hour(new_time)
        keyboard = [[InlineKeyboardButton("🔙 Назад до адмінки", callback_data="back_to_admin")]]
        
        if success:
            await update.message.reply_text(
                f"✅ Година `{new_time}` успішно додана в базу! Тепер клієнти бачать її при записі.", 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                f"⚠️ Помилка: слот `{new_time}` вже існує в базі даних.", 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

# --- ЗАПУСК ---
if __name__ == '__main__':
    threading.Thread(target=start_health_server, daemon=True).start()

    print("🤖 Запуск...", flush=True)
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Додаємо обробник тексту фільтром "тільки звичайний текст, не команди"
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("🚀 Бот онлайн!", flush=True)
    app.run_polling()