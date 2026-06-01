import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from barber_db import add_appointment

# --- ХАК ДЛЯ БЕЗКОШТОВНОГО RENDER ---
class HealthCheckServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is running safely and for free!")

def start_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckServer)
    server.serve_forever()
# -------------------------------------

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Твій Telegram ID для доступу до адмінки
ADMIN_ID = 1717915313 

# --- ФУНКЦІЇ БОТА ---

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if user_id == ADMIN_ID:
        # Створюємо реальні інлайн-кнопки для адміна
        keyboard = [
            [InlineKeyboardButton("➕ Додати вільний час", callback_data="admin_add_time")],
            [InlineKeyboardButton("❌ Видалити час", callback_data="admin_remove_time")],
            [InlineKeyboardButton("📋 Подивитися всі записи", callback_data="admin_view_appointments")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "👑 Вітаю в панелі Адміністратора!\nОберіть потрібну дію нижче:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("❌ У вас немає доступу до цієї команди.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("✂️ Записатися", callback_data="start_booking")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Вітаємо v Барбершопі 'NINJA'! 🥷\nНатисніть кнопку нижче, щоб обрати послугу та час.", 
        reply_markup=reply_markup
    )

# Обробка всіх натискань на кнопки (і клієнтських, і адмінських)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # --- КЛІЄНТСЬКА ЧАСТИНА ---
    # Крок 1: Вибір послуги
    if data == "start_booking":
        keyboard = [
            [InlineKeyboardButton("💇‍♂️ Чоловіча стрижка (500 грн)", callback_data="srv_Стрижка")],
            [InlineKeyboardButton("🧔 Моделювання бороди (300 грн)", callback_data="srv_Борода")],
            [InlineKeyboardButton("🔥 Комплекс: Стрижка + Борода (700 грн)", callback_data="srv_Комплекс")]
        ]
        await query.edit_message_text("Оберіть послугу:", reply_markup=InlineKeyboardMarkup(keyboard))

    # Крок 2: Вибір часу
    elif data.startswith("srv_"):
        service = data.split("_")[1]
        context.user_data['service'] = service 
        
        keyboard = [
            [InlineKeyboardButton("🕙 10:00", callback_data="time_10:00"),
             InlineKeyboardButton("🕛 12:00", callback_data="time_12:00")],
            [InlineKeyboardButton("🕒 15:00", callback_data="time_15:00"),
             InlineKeyboardButton("🕔 17:00", callback_data="time_17:00")],
            [InlineKeyboardButton("🔙 Назад", callback_data="start_booking")]
        ]
        await query.edit_message_text(f"Ви обрали: {service}. Тепер оберіть зручний час:", reply_markup=InlineKeyboardMarkup(keyboard))

    # Крок 3: Підтвердження запису клієнта
    elif data.startswith("time_"):
        time = data.split("_")[1]
        service = context.user_data.get('service', 'Невідома послуга')
        user_id = query.from_user.id
        username = query.from_user.username or query.from_user.first_name

        add_appointment(user_id, username, service, time)

        await query.edit_message_text(
            f"✅ Успішно!\n\nКлієнт: @{username}\nПослуга: {service}\nЧас: {time}\n\nЧекаємо на вас!"
        )

    # --- АДМІНСЬКА ЧАСТИНА (ОБРОБКА КНОПОК) ---
    elif data == "admin_add_time":
        # Тут згодом зробимо вибір годин для додавання в БД
        await query.edit_message_text("🔧 Кнопка працює! Функція додавання нових слотів часу зараз у розробці.")
        
    elif data == "admin_remove_time":
        # Тут буде видалення слотів
        await query.edit_message_text("🗑️ Кнопка працює! Логіку видалення робочих годин додамо наступним кроком.")
        
    elif data == "admin_view_appointments":
        # Тут зробимо виведення списку клієнтів з barber_db
        await query.edit_message_text("📋 Кнопка працює! Скоро налаштуємо вивантаження всіх актуальних записів із бази даних.")

# --- ЗАПУСК БОТА ---
if __name__ == '__main__':
    # Запускаємо веб-сервер для обходу обмежень безкоштовного тарифу Render
    threading.Thread(target=start_health_server, daemon=True).start()

    # Створюємо об'єкт бота
    app = ApplicationBuilder().token(TOKEN).build()

    # Реєструємо всі команди та кнопки
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Безкоштовний Барбер-бот з кнопками запущений!")
    app.run_polling()