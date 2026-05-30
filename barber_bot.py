import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from barber_db import add_appointment

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Головне меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("✂️ Записатися", callback_data="start_booking")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Вітаємо в Барбершопі 'NINJA'! 🥷\nНатисніть кнопку нижче, щоб обрати послугу та час.", 
        reply_markup=reply_markup
    )

# Обробка всіх натискань на кнопки
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

    # Крок 2: Вибір часу (спрацьовує, якщо обрали послугу)
    elif data.startswith("srv_"):
        service = data.split("_")[1]
        # Зберігаємо обрану послугу в тимчасову пам'ять
        context.user_data['service'] = service 
        
        keyboard = [
            [InlineKeyboardButton("🕙 10:00", callback_data="time_10:00"),
             InlineKeyboardButton("🕛 12:00", callback_data="time_12:00")],
            [InlineKeyboardButton("🕒 15:00", callback_data="time_15:00"),
             InlineKeyboardButton("🕔 17:00", callback_data="time_17:00")],
            [InlineKeyboardButton("🔙 Назад", callback_data="start_booking")]
        ]
        await query.edit_message_text(f"Ви обрали: {service}. Тепер оберіть зручний час:", reply_markup=InlineKeyboardMarkup(keyboard))

    # Крок 3: Підтвердження запису (спрацьовує, якщо обрали час)
    elif data.startswith("time_"):
        time = data.split("_")[1]
        service = context.user_data.get('service', 'Невідома послуга')
        user_id = query.from_user.id
        username = query.from_user.username or query.from_user.first_name

        # Зберігаємо в базу даних
        add_appointment(user_id, username, service, time)

        await query.edit_message_text(
            f"✅ Успішно!\n\nКлієнт: @{username}\nПослуга: {service}\nЧас: {time}\n\nЧекаємо на вас!"
        )

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))

print("Барбер-бот запущений!")
app.run_polling()