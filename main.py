import logging
import os
import io
import tempfile
import traceback

import cv2
import ffmpeg
from PIL import Image
from pillow_heif import HeifImagePlugin
from dotenv import load_dotenv

from datetime import datetime
from multiprocessing import Process

from telegram import Update, Message, File
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    CallbackContext,
    CommandHandler,
)

from showimage import show_image, show_mp4

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

required_env_vars = ["TELEGRAM_TOKEN", "ADMIN_USER_IDS"]

for env_var in required_env_vars:
    if env_var not in os.environ or os.environ[env_var] == "":
        raise Exception(f"Missing env var {env_var}")

admins = os.environ.get("ADMIN_USER_IDS").split(",")
logger.info("Active admins: " + (",".join(admins)))

matrix_process: Process = None
message_queue = []
last_message_processed_timestamp = 0


def get_message_type(message: Message):
    if message.document and message.document.mime_type:
        if message.document.mime_type == "video/mp4":
            return "attachment_video"
        elif "image" in message.document.mime_type:
            return "attachment_image"
    elif message.photo:
        return "photo"
    elif message.video:
        return "video"
    elif message.sticker:
        if message.sticker.is_animated:
            return "sticker_animation"
        if message.sticker.is_video:
            return "sticker_video"
        else:
            return "sticker_static"


#
#   Functions for sending stuff to the matrix
#


async def display_video(file: File):
    try:
        global matrix_process, last_message_processed_timestamp

        with io.BytesIO() as out:
            await file.download_to_memory(out)
            out.seek(0)

            with (
                tempfile.NamedTemporaryFile() as tempf,
                tempfile.NamedTemporaryFile() as tempf2,
            ):
                tempf.write(out.read())

                capture = cv2.VideoCapture(tempf.name)
                width = capture.get(3)
                height = capture.get(4)
                capture.release()
                resized = False
                if width % 2 != 0 or height % 2 != 0:
                    ffmpeg.input(tempf.name).filter(
                        "scale",
                        width - 1 if width % 2 != 0 else width,
                        height - 1 if height % 2 != 0 else height,
                    ).output(tempf2.name, format="mp4").overwrite_output().run()
                    resized = True

                capture = cv2.VideoCapture(tempf.name if not resized else tempf2.name)
                frames = []

                while capture.isOpened():
                    return_value, image = capture.read()
                    if return_value:
                        converted = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                        pil_image = Image.fromarray(converted)
                        pil_image.thumbnail((64, 64), Image.Resampling.LANCZOS)
                        frames.append(pil_image.convert("RGB"))
                    elif not return_value:
                        break

                capture.release()

                if matrix_process is not None:
                    matrix_process.kill()
                matrix_process = Process(target=show_mp4, args=(frames,))
                matrix_process.start()
    except Exception as error:
        logger.error(f"Video processing error {error}")
    finally:
        if message_queue:
            last_message_processed_timestamp = datetime.now().timestamp()
            application.job_queue.run_once(check_next_image, 15)


async def display_image(file: File):
    global matrix_process, last_message_processed_timestamp
    try:
        with io.BytesIO() as out:
            await file.download_to_memory(out)
            out.seek(0)

            with Image.open(out) as image:
                image.thumbnail((64, 64))
                image = image.convert("RGB")

                if matrix_process is not None:
                    matrix_process.kill()
                matrix_process = Process(target=show_image, args=(image,))
                matrix_process.start()
    except Exception as error:
        logger.error(f"Image processing error {error}")
    finally:
        if message_queue:
            last_message_processed_timestamp = datetime.now().timestamp()
            application.job_queue.run_once(check_next_image, 15)


#
#   Functions for digging out bits to display from messages
#


async def process_attachment_image(message: Message):
    await display_image(await message.document.get_file())


async def process_photo(message: Message):
    await display_image(await message.effective_attachment[-1].get_file())


async def process_video(message: Message):
    await display_video(await message.video.get_file())


async def process_attachment_video(message: Message):
    await display_video(await message.document.get_file())


async def process_static_sticker(message: Message):
    await display_image(await message.sticker.get_file())


async def process_animated_or_video_sticker(message: Message):
    await display_video(await message.sticker.get_file())


#
#   Telegram message handlers
#


async def handle_message(update: Update, context: CallbackContext):
    logger.info(f"Got message {update.message}")

    message_type = get_message_type(update.message)
    logger.info(f"Message type {message_type}")

    global matrix_process, message_queue, last_message_processed_timestamp

    if message_type:
        message_queue.append({"message_type": message_type, "message": update.message})
        time_delta = datetime.now().timestamp() - last_message_processed_timestamp
        print(time_delta)
        print(len(message_queue))
        if len(message_queue) <= 1 and time_delta > 15:
            logger.info(
                "Queue empty or previous message is old, displaying immediately"
            )
            await check_next_image()

    else:
        logger.warning("Unhandled message type")
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Sori ei pysty"
        )


async def handle_skip(update: Update, context: CallbackContext):
    if matrix_process is not None:
        matrix_process.kill()

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Skipping image"
    )


async def handle_queue(update: Update, context: CallbackContext):
    if matrix_process is not None:
        matrix_process.kill()

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Here are the queued images"
    )

    [
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"{message.sender} {message.image}"
        )
        for message in [
            {"sender": "jaripekka", "image": "asd.png"},
            {"sender": "joosua", "image": "asdasd.png"},
        ]
    ]


async def check_next_image(context=None) -> None:
    logging.info("Checking next image in queue")

    global message_queue

    if len(message_queue) == 0:
        logging.info("No messages")
    else:
        message = message_queue[0]
        logging.info(f"Processing next message {message}")

        match message["message_type"]:
            case "attachment_image":
                await process_attachment_image(message["message"])
            case "attachment_video":
                await process_attachment_video(message["message"])
            case "photo":
                await process_photo(message["message"])
            case "video":
                await process_video(message["message"])
            case "sticker_animation" | "sticker_video":
                await process_animated_or_video_sticker(message["message"])
            case "sticker_static":
                await process_static_sticker(message["message"])

        message_queue.pop(0)


if __name__ == "__main__":
    application = ApplicationBuilder().token(os.environ.get("TELEGRAM_TOKEN")).build()

    application.add_handler(
        MessageHandler(filters.ChatType.PRIVATE & (~filters.TEXT), handle_message)
    )
    application.add_handler(CommandHandler("skip", handle_skip))
    # application.add_handler(CommandHandler("queue", handle_skip))

    try:
        application.run_polling()
    except Exception as e:
        logging.error(e)
        logging.error(traceback.format_exc())
    finally:
        if matrix_process:
            matrix_process.kill()
