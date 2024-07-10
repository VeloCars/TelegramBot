# Import Libraries
import uuid
from telegram import Update, InputMediaPhoto, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from typing import Final
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time
from telegram.error import TimedOut

# Constants
BOT_USERNAME: Final = "@velocars_bot"
TOKEN: Final = "6950868494:AAGSpVty3TiuLD8mItNeRLY7GGxN0kqfyBg"
GOOGLE_SHEETS_CREDENTIALS = "/Users/aliemirkaragulle/Desktop/velo-telegram-158adc10d37e.json"
FOLDER_ID = "1XjNOWyEcQ5al-ip3wFaYWD78UxtY5ZJW"

# Conversation States
(
    NAME, SURNAME, EMAIL, PHONE_NUMBER, USERNAME, PREFERRED_CHANNEL, CAR_PHOTOS,
    CAR_BRAND, CAR_MODEL, CAR_YEAR, CAR_KM, FUEL_TYPE, TRANSMISSION, CAR_PRICE, CAR_LOCATION,
    VEHICLE_ID, BOOKING_DATES
) = range(17)



# Commands
# /start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "🚗 Welcome To Velo, The Ultimate Peer-To-Peer Car Sharing Platform! \n\n"
        "Here’s How You Can Dive In And Make The Most Of Our Services:\n"
        "- 📝 Register: Get Started By Sending /register To Create Your User Profile.\n"
        "- 🚗 List Your Vehicle: Have A Vehicle To Rent Out? Send /listvehicle To Add Your Vehicle To Our Platform.\n"
        "- 🔍 View Available Vehicles: Looking For A Ride? Send /viewvehicle To See All Available Vehicles Near You.\n"
        "- 📅 Book A Vehicle: Found The Perfect Ride? Use /bookvehicle To Reserve It For Your Next Trip.\n"
        "- ❓ Need Help: Questions Or Need Assistance? Send /help For More Information About Our Services.\n\n"
        "Drive Your Way, Earn Your Pay With Velo! 🚙💨"
    )
    await update.message.reply_text(welcome_message)

# /register command
async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    if is_user_registered(user_id):
        await update.message.reply_text(
            "You are already registered! 😊\n\n"
            "To view available cars for rent, send the command /viewvehicle. \n"
            "To list your own vehicle on the platform, send the command /listvehicle."
        )
        return ConversationHandler.END
    await update.message.reply_text("Please Enter Your First Name:", reply_markup=ReplyKeyboardRemove())
    return NAME

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text.title()
    await update.message.reply_text('Great! Now, Please Enter Your Surname:')
    return SURNAME

async def surname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['surname'] = update.message.text.title()
    await update.message.reply_text('Great! Now, Please Enter Your Email Address:')
    return EMAIL

async def email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['email'] = update.message.text
    await update.message.reply_text('Great! Now, Please Enter Your Phone Number, Starting with the + Followed by Your Country Code:')
    return PHONE_NUMBER

async def phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['phone_number'] = update.message.text
    await update.message.reply_text("Great! Now, Please Enter Your Telegram Username. To find or create your username, go back from the chat, press 'Settings', and look for 'Username':")
    return USERNAME

async def username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data
    username = update.message.text.strip()
    if not username.startswith('@'):
        username = '@' + username
    user_data['username'] = username

    reply_keyboard = [['1: Phone', '2: Email', '3: Telegram Username']]
    await update.message.reply_text(
        'Please Choose Your Preferred Communication Channel:\n1: Phone\n2: Email\n3: Telegram Username',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return PREFERRED_CHANNEL

async def preferred_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data
    preferred_channel = update.message.text.split(':')[0]
    user_data['preferred_channel'] = preferred_channel

    user_id = update.message.from_user.id
    add_user_data(user_id, user_data['name'], user_data['surname'], user_data['email'], user_data['phone_number'], user_data['username'], user_data['preferred_channel'])

    await update.message.reply_text(
        "Thank you for registering! Your details have been saved. 🎉\n\n"
        "To view available cars for rent, send the command /viewvehicle.\n"
        "To list your own vehicle on the platform, send the command /listvehicle."
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Registration Cancelled.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# /listvehicle command
async def list_vehicle_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    if not is_user_registered(user_id):
        await update.message.reply_text('You need to register first by using /register.')
        return ConversationHandler.END

    context.user_data['vehicle_id'] = str(uuid.uuid4())
    context.user_data['car_photos'] = []

    await update.message.reply_text("Please Send Photos Of Your Car. Click /here When Finished:")
    return CAR_PHOTOS

async def car_photos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    photos = update.message.photo
    if not photos:
        await update.message.reply_text('Please Send Photos Of Your Car.')
        return CAR_PHOTOS

    file_id = photos[-1].file_id
    context.user_data['car_photos'].append(file_id)

    return CAR_PHOTOS

async def here_photos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Great! Now, Please Enter the Brand Of Your Car:')
    return CAR_BRAND

async def car_brand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['car_brand'] = update.message.text.title()
    await update.message.reply_text('Great! Now, Please Enter The Model Of Your Car:')
    return CAR_MODEL

async def car_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['car_model'] = update.message.text.title()
    await update.message.reply_text('Please Enter The Year Of Your Car:')
    return CAR_YEAR

async def car_year(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['car_year'] = update.message.text
    await update.message.reply_text('Please Enter The Km Of Your Car:')
    return CAR_KM

async def car_km(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['car_km'] = update.message.text
    await update.message.reply_text('Please Choose The Fuel Type Of Your Car:\n1: Gasoline\n2: Diesel\n3: Electric', reply_markup=ReplyKeyboardMarkup([['1: Gasoline', '2: Diesel', '3: Electric']], one_time_keyboard=True))
    return FUEL_TYPE

async def fuel_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['fuel_type'] = update.message.text.split(':')[1].strip()
    await update.message.reply_text('Please Choose The Transmission Of Your Car:\n1: Automatic\n2: Manual', reply_markup=ReplyKeyboardMarkup([['1: Automatic', '2: Manual']], one_time_keyboard=True))
    return TRANSMISSION

async def transmission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['transmission'] = update.message.text.split(':')[1].strip()
    await update.message.reply_text('Please Enter The Daily Price Of Your Car in Euros (Numbers Only):')
    return CAR_PRICE

async def car_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    price_text = update.message.text
    try:
        price = float(price_text)
        context.user_data['car_price'] = price
        await update.message.reply_text('Please Enter The Location Of Your Car:')
        return CAR_LOCATION
    except ValueError:
        await update.message.reply_text('Invalid Price Format. Please Enter the Daily Price of Your Car as a Number:')
        return CAR_PRICE

async def car_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data
    user_data['car_location'] = update.message.text.title()
    user_id = update.message.from_user.id
    vehicle_id = user_data['vehicle_id']

    add_vehicle_data(
        vehicle_id, user_id, user_data['car_photos'], user_data['car_brand'], user_data['car_model'], user_data['car_year'],
        user_data['car_km'], user_data['fuel_type'], user_data['transmission'], user_data['car_price'], user_data['car_location']
    )

    await update.message.reply_text('Your Vehicle Has Been Listed!')
    return ConversationHandler.END


# /viewvehicle
async def view_vehicle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    vehicles = get_all_vehicles()
    if vehicles:
        for vehicle in vehicles:
            vehicle_id, user_id, photos, brand, model, year, km, fuel_type, transmission, price, location, booked = vehicle
            photo_ids = photos.split(",")
            media_group = [InputMediaPhoto(media=file_id) for file_id in photo_ids]

            sent_successfully = False
            while not sent_successfully:
                try:
                    await update.message.reply_media_group(media_group)
                    sent_successfully = True
                except TimedOut:
                    time.sleep(3)  # Wait for 3 Seconds Before Retrying

            await update.message.reply_text("Vehicle ID (The Number Below):")
            await update.message.reply_text(f"{vehicle_id}")
            await update.message.reply_text(
                f"Brand: {brand}\nModel: {model}\nYear: {year}\nKM: {km}\nFuel Type: {fuel_type}\nTransmission: {transmission}\nPrice: {price}\nLocation: {location}\nBooked: {booked}"
            )
        await update.message.reply_text("To book any of these cars, please send the command /bookvehicle and follow the instructions.")
    else:
        await update.message.reply_text("No Vehicles Available At The Moment.")


# /bookvehicle command
async def book_vehicle_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    if not is_user_registered(user_id):
        await update.message.reply_text('You need to register first by using /register.')
        return ConversationHandler.END

    await update.message.reply_text("Please Enter The Vehicle ID Of The Car You Want To Book:")
    return VEHICLE_ID

async def vehicle_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['vehicle_id'] = update.message.text
    await update.message.reply_text("Please Enter The Dates You Want To Book The Vehicle (DD/MM/YYYY - DD/MM/YYYY):")
    return BOOKING_DATES

async def booking_dates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    booking_dates = update.message.text
    splitted_booking_dates = booking_dates.split("-")
    booking_dates = splitted_booking_dates[0].strip() + " - " + splitted_booking_dates[1].strip()

    vehicle_id = context.user_data['vehicle_id']
    renter_id = update.message.from_user.id

    # Debugging Prints
    print(f"Vehicle ID: {vehicle_id}")
    print(f"Booking Dates: {booking_dates}")
    print(f"Renter ID: {renter_id}")

    contact_info, preferred_channel = book_vehicle(vehicle_id, booking_dates, renter_id)

    # Debugging Prints
    print(f"Contact Info: {contact_info}")
    print(f"Preferred Channel: {preferred_channel}")

    if contact_info:
        preferred_channel_str = {
            "1": "Phone",
            "2": "Email",
            "3": "Telegram Username"
        }.get(preferred_channel, "Unknown")
        await update.message.reply_text(
            f"The Vehicle Has Been Booked! The Owner's Preferred Contact Information is {preferred_channel_str}: {contact_info}"
        )
    else:
        await update.message.reply_text("Vehicle ID Not Found.")
    return ConversationHandler.END


# /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = "Need Help? 🤔 If You Have Any Questions Or Need Support, Please Don't Hesitate To Contact Us Via Email At velocarshare@gmail.com.\n\n"
    await update.message.reply_text(help_message)



# Responses
def handle_response(text: str) -> str:
    processed: str = text.lower()
    return "Hello. Please send the /start command."

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f"User ({update.message.chat.id}) in {message_type}: '{text}'")

    if message_type == "group":
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, "").strip()
            response: str = handle_response(new_text)
        else:
            return
    else:
        response: str = handle_response(text)

    print("Bot:", response)
    await update.message.reply_text(response)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")



# Database
# Initialize Google Sheets Client
def auth_gspread():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDENTIALS, scope)
    client = gspread.authorize(creds)
    return client

def add_user_data(user_id, name, surname, email, phone_number, username, preferred_channel):
    client = auth_gspread()
    sheet = client.open("VeloDB").worksheet("VeloUserDB")
    user_data = [user_id, name, surname, email, phone_number, username, preferred_channel]
    sheet.append_row(user_data)

def is_user_registered(user_id) -> bool:
    client = auth_gspread()
    sheet = client.open("VeloDB").worksheet("VeloUserDB")
    users = sheet.col_values(1)
    return str(user_id) in users

def add_vehicle_data(vehicle_id, user_id, photos, brand, model, year, km, fuel_type, transmission, price, location):
    client = auth_gspread()
    sheet = client.open("VeloDB").worksheet("VeloVehicleDB")
    vehicle_data = [vehicle_id, user_id, ",".join(photos), brand, model, year, km, fuel_type, transmission, price, location, "No"]
    sheet.append_row(vehicle_data)

def get_all_vehicles():
    client = auth_gspread()
    sheet = client.open("VeloDB").worksheet("VeloVehicleDB")
    vehicles = sheet.get_all_values()
    return vehicles[1:]

def book_vehicle(vehicle_id, booking_dates, renter_id):
    client = auth_gspread()
    vehicle_sheet = client.open("VeloDB").worksheet("VeloVehicleDB")
    transaction_sheet = client.open("VeloDB").worksheet("Transactions")
    user_sheet = client.open("VeloDB").worksheet("VeloUserDB")
    vehicles = vehicle_sheet.get_all_values()

    for i, vehicle in enumerate(vehicles):
        if vehicle[0] == vehicle_id:
            owner_id = vehicle[1]
            price = float(vehicle[9])

            # Calculate Number of Days
            start_date_str, end_date_str = booking_dates.split(" - ")
            start_date = datetime.strptime(start_date_str, "%d/%m/%Y")
            end_date = datetime.strptime(end_date_str, "%d/%m/%Y")
            number_of_days = (end_date - start_date).days 

            total_price = price * number_of_days
            date_of_order = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            vehicle_sheet.update_cell(i + 1, len(vehicle), f"Yes, from {booking_dates}")

            # Add Transaction to Transactions Sheet
            transaction_data = [owner_id, renter_id, vehicle_id, price, number_of_days, total_price, booking_dates, date_of_order]
            transaction_sheet.append_row(transaction_data)

            # Find Owner's Contact Information
            users = user_sheet.get_all_values()
            for user in users:
                if user[0] == owner_id:
                    preferred_channel = user[6]  # Preferred Channel is in the Seventh Column
                    contact_info_column = {
                        "1": 4,  # Phone Number Column
                        "2": 3,  # Email Column
                        "3": 5   # Telegram Username Column
                    }.get(preferred_channel, None)

                    if contact_info_column:
                        contact_info = user[contact_info_column]
                        return contact_info, preferred_channel
    return None, None



if __name__ == "__main__":
    print("Starting Bot...")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))

    register_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('register', register_command)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            SURNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, surname)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
            PHONE_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone_number)],
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, username)],
            PREFERRED_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, preferred_channel)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    app.add_handler(register_conv_handler)

    list_vehicle_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('listvehicle', list_vehicle_command)],
        states={
            CAR_PHOTOS: [MessageHandler(filters.PHOTO, car_photos), CommandHandler('here', here_photos)],
            CAR_BRAND: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_brand)],
            CAR_MODEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_model)],
            CAR_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_year)],
            CAR_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_km)],
            FUEL_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, fuel_type)],
            TRANSMISSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, transmission)],
            CAR_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_price)],
            CAR_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_location)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    app.add_handler(list_vehicle_conv_handler)

    app.add_handler(CommandHandler("viewvehicle", view_vehicle_command))

    book_vehicle_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('bookvehicle', book_vehicle_command)],
        states={
            VEHICLE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, vehicle_id)],
            BOOKING_DATES: [MessageHandler(filters.TEXT & ~filters.COMMAND, booking_dates)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    app.add_handler(book_vehicle_conv_handler)

    app.add_handler(CommandHandler("help", help_command))

    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    app.add_error_handler(error)

    print("Polling...")
    app.run_polling(poll_interval=1)