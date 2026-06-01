import os
import threading
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
# Імпортуємо функцію витягу записів разом із додаванням
from barber_db import add_appointment, get_all_appointments

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
    print(f"🌍 Мікро-сервер запускається на порту {port}...", flush=True)
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckServer)
        print(f"✅ Мікро-сервер успішно перевіряє порт {port}!", flush=True)
        server.serve_forever()
    except Exception as e:
        print(f"❌ Помилка мікро-сервера: {e}", flush=True)
# -------------------------------------

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ КРИТИЧНА ПОМИЛКА: BOT_TOKEN не знайдено в налаштуваннях Render!", flush=True)
    sys.exit(1)

# Твій Telegram ID для доступу до адмінки
ADMIN_ID = 1717915313 

# --- ФУНКЦІЇ БОТА ---

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if user_id == ADMIN_ID:
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

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # --- КЛІЄНТСЬКА ЧАСТИНА ---
    if data == "start_booking":
        keyboard = [
            [InlineKeyboardButton("💇‍♂️ Чоловіча стрижка (500 грн)", callback_data="srv_Стрижка")],
            [InlineKeyboardButton("🧔 Моделювання бороди (300 грн)", callback_data="srv_Борода")],
            [InlineKeyboardButton("🔥 Комплекс: Стрижка + Борода (700 грн)", callback_data="srv_Комплекс")]
        ]
        await query.edit_message_text("Оберіть послугу:", reply_markup=InlineKeyboardMarkup(keyboard))

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

    elif data.startswith("time_"):
        time = data.split("_")[1]
        service = context.user_data.get('service', 'Невідома послуга')
        user_id = query.from_user.id
        username = query.from_user.username or query.from_user.first_name

        add_appointment(user_id, username, service, time)

        await query.edit_message_text(
            f"✅ Успішно!\n\nКлієнт: @{username}\nПослуга: {service}\nЧас: {time}\n\nЧекаємо на вас!"
        )

    # --- АДМІНСЬКА ЧАСТИНА ---
    
    # Кнопка повернення в головне меню адмінки
    elif data == "back_to_admin":
        keyboard = [
            [InlineKeyboardButton("➕ Додати вільний час", callback_data="admin_add_time")],
            [InlineKeyboardButton("❌ Видалити час", callback_data="admin_remove_time")],
            [InlineKeyboardButton("📋 Подивитися всі записи", callback_data="admin_view_appointments")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "👑 Вітаю в панелі Адміністратора!\nОберіть потрібну дію нижче:",
            reply_markup=reply_markup
        )

    elif data == "admin_add_time":
        keyboard = [[InlineKeyboardButton("🔙 Назад до адмінки", callback_data="back_to_admin")]]
        await query.edit_message_text(
            "🔧 Функція додавання нових слотів часу зараз у розробці.", 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    elif data == "admin_remove_time":
        keyboard = [[InlineKeyboardButton("🔙 Назад до адмінки", callback_data="back_to_admin")]]
        await query.edit_message_text(
            "🗑️ Логіку видалення робочих годин додамо наступним кроком.", 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    elif data == "admin_view_appointments":
        keyboard = [[InlineKeyboardButton("🔙 Назад до адмінки", callback_data="back_to_admin")]]
        
        try:
            # Отримуємо записи з бази даних
            records = get_all_appointments()
            
            if not records:
                report_text = "📋 Наразі немає жодних записів клієнтів у базі."
            else:
                report_text = "📋 Актуальні записи на сьогодні:\n\n"
                for row in records:
                    # row[0] - username, row[1] - service, row[2] - time
                    report_text += f"⏰ {row[2]} — @{row[0]} ({row[1]})\n"
                    
        except Exception as e:
            report_text = f"❌ Помилка при читанні бази даних: {e}"
            
        await query.edit_message_text(report_text, reply_markup=InlineKeyboardMarkup(keyboard))

# --- ЗАПУСК ---
if __name__ == '__main__':
    threading.Thread(target=start_health_server, daemon=True).start()

    print("🤖 Ініціалізація Telegram бота...", flush=True)
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🚀 Безкоштовний Барбер-бот успішно запущений і готовий до роботи!", flush=True)
    app.run_polling()