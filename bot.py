import logging
from dotenv import load_dotenv
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler,
)
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
# from textwrap import wrap
from PIL import Image
from collections import defaultdict
import time

# Load the .env file
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

# Directory for temporary storage
TEMP_DIR = "temp_files"

# Ensure the directory exists
os.makedirs(TEMP_DIR, exist_ok=True)

# Cache to store media groups temporarily
media_group_cache = defaultdict(list)


def start(update: Update, context: CallbackContext) -> None:
    """Handle the /start command."""
    # keyboard = [
    #     [InlineKeyboardButton("Clear", callback_data='clear')],
    #     [InlineKeyboardButton("Convert", callback_data='convert')]
    # ]
    # reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "Hello! Send me images or text files, and I'll convert them into a PDF for you.\n"
        "To start, simply upload files, and I'll take care of the rest!\n"
        "Supported file formats: .txt, .doc, .docx, .odt, .md, .jpg, .webp, .png"
    )
    # update.message.reply_text("Choose an action:", reply_markup=reply_markup)


def handle_message(update: Update, context: CallbackContext) -> None:

    # Check if the message is part of a media group
    media_group_id = update.message.media_group_id
    if media_group_id:
        # Add message to the cache
        media_group_cache[media_group_id].append(update.message)

        # Wait briefly to ensure all files are received
        time.sleep(2)

        # Check if we have all messages in the group
        if len(media_group_cache[media_group_id]) > 1:
            # logging.warning(
            #     f"Detected {len(media_group_cache[media_group_id])} files in the media group."
            # )

            # Process files
            for msg in media_group_cache[media_group_id]:
                photo = msg.photo
                document = msg.document

                if photo:
                    # Get the largest available photo
                    file_id = photo[-1].file_id
                    file_name = f"{file_id}.jpg"
                    # Download the file
                    file_path = os.path.join(TEMP_DIR, file_name)
                    photo = photo[-1].get_file()
                    photo.download(file_path)
                    # Save the file path in the user context
                    if "files" not in context.user_data:
                        context.user_data["files"] = []
                    context.user_data["files"].append(file_path)
                    # logging.warning("Photo name:" + file_name)
                elif (
                    document
                    and document.mime_type
                    and document.mime_type.startswith("image/")
                ):
                    # Handle image files sent as documents
                    file_id = document.file_id
                    file_name = document.file_name or f"{file_id}.webp"
                    # Download the file
                    file_path = os.path.join(TEMP_DIR, file_name)
                    document = document.get_file()
                    document.download(file_path)
                    # Save the file path in the user context
                    if "files" not in context.user_data:
                        context.user_data["files"] = []
                    context.user_data["files"].append(file_path)
                    # logging.warning("Image document name:" + file_name)
                elif document:
                    # Handle image files sent as documents
                    file_name = document.file_name
                    file_extension = os.path.splitext(file_name)[1].lower()
                    # Check for supported file types
                    if file_extension not in [".txt", ".doc", ".docx", ".odt", ".md"]:
                        update.message.reply_text(
                            "Unsupported file type. Please upload .txt, .doc, .docx, .odt, .md, .jpg, .webp or .png files."
                        )
                        return
                    # Download the file
                    file_path = os.path.join(TEMP_DIR, file_name)
                    document = document.get_file()
                    document.download(file_path)
                    # Save the file path in the user context
                    if "files" not in context.user_data:
                        context.user_data["files"] = []
                    context.user_data["files"].append(file_path)
                    # logging.warning("Document name:" + file_name)
                else:
                    update.message.reply_text("Please send a valid file.")
                    return

            # convert_to_pdf(update, context)
            # Respond with buttons
            update.message.reply_text(
                "Files saved. What would you like to do next?",
                reply_markup=get_buttons(),
            )
            # Clear the cache for this media group
            del media_group_cache[media_group_id]
    else:
        # Handle single file/message
        photo = update.message.photo
        document = update.message.document

        if photo:
            # Get the largest available photo
            file_id = photo[-1].file_id
            file_name = f"{file_id}.jpg"
            # Download the file
            file_path = os.path.join(TEMP_DIR, file_name)
            photo = photo[-1].get_file()
            photo.download(file_path)
            # Save the file path in the user context
            if "files" not in context.user_data:
                context.user_data["files"] = []
            context.user_data["files"].append(file_path)
            # convert_to_pdf(update, context)
            # Respond with buttons
            update.message.reply_text(
                "Files saved. What would you like to do next?",
                reply_markup=get_buttons(),
            )
            # logging.warning("Photo name:" + file_name)
        elif (
            document and document.mime_type and document.mime_type.startswith("image/")
        ):
            # Handle image files sent as documents
            file_id = document.file_id
            file_name = document.file_name or f"{file_id}.webp"
            # Download the file
            file_path = os.path.join(TEMP_DIR, file_name)
            document = document.get_file()
            document.download(file_path)
            # Save the file path in the user context
            if "files" not in context.user_data:
                context.user_data["files"] = []
            context.user_data["files"].append(file_path)
            # convert_to_pdf(update, context)
            # Respond with buttons
            update.message.reply_text(
                "Files saved. What would you like to do next?",
                reply_markup=get_buttons(),
            )
            # logging.warning("Image document name:" + file_name)
        elif document:
            # Handle image files sent as documents
            file_name = document.file_name
            file_extension = os.path.splitext(file_name)[1].lower()
            # Check for supported file types
            if file_extension not in [".txt", ".doc", ".docx", ".odt", ".md"]:
                update.message.reply_text(
                    "Unsupported file type. Please upload .txt, .doc, .docx, .odt, .md, .jpg, .webp or .png files."
                )
                return
            # Download the file
            file_path = os.path.join(TEMP_DIR, file_name)
            document = document.get_file()
            document.download(file_path)
            # Save the file path in the user context
            if "files" not in context.user_data:
                context.user_data["files"] = []
            context.user_data["files"].append(file_path)
            # convert_to_pdf(update, context)
            # Respond with buttons
            update.message.reply_text(
                "Files saved. What would you like to do next?",
                reply_markup=get_buttons(),
            )
            # logging.warning("Document name:" + file_name)
        else:
            update.message.reply_text("Please send a valid file.")
            return


# Create a PDF
def convert_to_pdf(update: Update, context: CallbackContext) -> None:
    """Convert uploaded files to a single PDF."""
    if "files" not in context.user_data or not context.user_data["files"]:
        update.callback_query.message.reply_text(
            "No files to convert. Please upload files first."
        )
        return

    pdf_path = os.path.join(TEMP_DIR, "output.pdf")

    try:
        # Create a canvas
        c = canvas.Canvas(pdf_path, pagesize=A4)
        c.setFont("Helvetica", 12)
        width, height = A4

        # Define margin and line height
        margin = 50
        line_height = 14

        # Start near the top of the page
        x, y = margin, height - margin

        for file_path in context.user_data["files"]:
            file_extension = os.path.splitext(file_path)[1].lower()

            if file_extension in [".txt", ".doc", ".docx", ".odt", ".md"]:
                # Add text file content to the PDF
                with open(file_path, "r", encoding="utf-8") as f:
                    # Draw the wrapped text
                    for line in f:
                        # Handle empty lines explicitly
                        if line.strip() == "":
                            y -= line_height
                            if (
                                y < margin
                            ):  # If space is insufficient, create a new page
                                c.showPage()
                                c.setFont("Helvetica", 12)
                                y = height - margin
                            continue

                        # Split long lines to fit the page width
                        wrapped_lines = simpleSplit(
                            line.strip(), "Helvetica", 12, width - 2 * margin
                        )
                        for wrapped_line in wrapped_lines:
                            if (
                                y < margin
                            ):  # If space is insufficient, create a new page
                                c.showPage()
                                c.setFont("Helvetica", 12)
                                y = height - margin
                            c.drawString(x, y, wrapped_line)
                            y -= line_height
                    c.showPage()

            elif file_extension in [".jpg", ".jpeg", ".png", ".webp"]:
                # Add an image to the PDF
                img = Image.open(file_path)
                img_width, img_height = img.size
                # Scale the image proportionally if it's larger than A4
                if img_width > width - margin or img_height > height - margin:
                    img.thumbnail((width - margin, -margin), Image.Resampling.LANCZOS)
                # Calculate position to center the image
                paste_x = (width - img.width) // 2
                paste_y = (height - img.height) // 2
                c.drawImage(file_path, paste_x, paste_y, img.width, img.height)
                c.showPage()  # New page for each image

        c.save()
        update.callback_query.message.reply_text("Here's your PDF ^^")
        update.callback_query.message.reply_document(
            open(pdf_path, "rb"), filename="output.pdf"
        )
    except Exception as e:
        update.callback_query.message.reply_text(f"An error occurred: {e}")
    finally:
        # Clean up
        for file_path in context.user_data["files"]:
            os.remove(file_path)
        context.user_data["files"] = []


def clear_files(update: Update, context: CallbackContext) -> None:
    """Clear all uploaded files from the user session."""
    media_group_cache = defaultdict(list)
    if "files" in context.user_data:
        for file_path in context.user_data["files"]:
            os.remove(file_path)
        context.user_data["files"] = []
    update.callback_query.message.reply_text("All uploaded files have been cleared.")


def get_buttons():
    """Return the keyboard with 'Clear' and 'Convert' buttons."""
    keyboard = [
        [InlineKeyboardButton("Clear", callback_data="clear")],
        [InlineKeyboardButton("Convert", callback_data="convert")],
    ]
    return InlineKeyboardMarkup(keyboard)


def main():
    # Set up the updater and dispatcher
    updater = Updater(API_TOKEN)
    dispatcher = updater.dispatcher

    # Command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("convert", convert_to_pdf))
    dispatcher.add_handler(CommandHandler("clear", clear_files))

    # CallbackQuery handler for button presses
    dispatcher.add_handler(CallbackQueryHandler(clear_files, pattern="^clear$"))
    dispatcher.add_handler(CallbackQueryHandler(convert_to_pdf, pattern="^convert$"))

    # Message handler for files (photos, documents)
    dispatcher.add_handler(
        MessageHandler(Filters.document | Filters.photo, handle_message)
    )

    # Start the bot
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
