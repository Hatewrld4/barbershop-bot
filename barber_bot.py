import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from barber_db import add_appointment

# Завантажуємо токен
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Твій Telegram ID для доступу до адмінки
ADMIN_ID = 1717915313 

# --- ФУНКЦІЇ БОТА ---

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if user_id == ADMIN_ID:
        await update.message.reply_text(
            "👑 Вітаю в панелі Адміністратора!\n\n"
            "Тут ми зробимо кнопки:\n"
            "1. ➕ Додати вільний час\n"
            "2. ❌ Видалити час\n"
            "3. 📋 Подивитися всі записи на сьогодні"
        )
    else:
        await update.message.reply_text("❌ У вас немає доступу до цієї команди.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("✂️ Записатися", callback_data="start_booking")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Вітаємо в Барбершопі 'NINJA'! 🥷\nНатисніть кнопку нижче, щоб обрати послугу та час.", 
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

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

    # Крок 3: Підтвердження запису
    elif data.startswith("time_"):
        time = data.split("_")[1]
        service = context.user_data.get('service', 'Невідома послуга')
        user_id = query.from_user.id
        username = query.from_user.username or query.from_user.first_name

        add_appointment(user_id, username, service, time)

        await query.edit_message_text(
            f"✅ Успішно!\n\nКлієнт: @{username}\nПослуга: {service}\nЧас: {time}\n\nЧекаємо на вас!"
        )

# --- ЗАПУСК БОТА ---
if __name__ == '__main__':
    # Створюємо об'єкт бота
    app = ApplicationBuilder().token(TOKEN).build()

    # Реєструємо всі команди та кнопки (саме тут їхнє правильне місце)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Барбер-бот запущений!")
    
    # Запускаємо процес
    app.run_polling()