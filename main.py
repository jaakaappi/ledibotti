import logging
import os
import io
import tempfile
import traceback

import cv2
import ffmpeg
from PIL import Image
from dotenv import load_dotenv

# from lottie.exporters.gif import export_gif
# from lottie.importers.core import import_tgs
from telegram import Update, Message
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    CallbackContext,
    CommandHandler,
)
from multiprocessing import Process

from showimage import show_image, show_mp4

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

required_env_vars = ["TELEGRAM_TOKEN", "ADMIN_USER_IDS"]
matrix_process: Process = None

for env_var in required_env_vars:
    if env_var not in os.environ or os.environ[env_var] == "":
        raise Exception(f"Missing env var {env_var}")

admins = os.environ.get("ADMIN_USER_IDS").split(",")

logger.info("Active admins: " + (",".join(admins)))


# def get_image_file_type(message: Message):
#     # todo handle photos, stickers
#     if message.animation is not None:
#         print("animation")
#         return message.animation.file_id
#     elif len(message.photo) > 0:
#         print("photo")
#         return message.photo[-1].file_id
#     if hasattr(message, "sticker"):
#         print("sticker")
#         return message.sticker.file_id


def get_message_type(message):
    if message.document and message.document.mime_type:
        if message.document.mime_type == "video/mp4":
            return "attachment_video"
        elif (
            "image" in message.document.mime_type
            and "heic" not in message.document.mime_type
        ):
            return "attachment_image"


async def handle_image(update: Update, context: CallbackContext):
    print(update.message)

    message_type = get_message_type(update.message)
    print(message_type)

    global matrix_process

    if message_type == "attachment_image":
        if update.message.document and update.message.document.file_size > 1000000000:
            logger.error(
                f"Too big file: {update.message.document.file_name} {update.message.document.file_size/1000}MB"
            )

        with io.BytesIO() as out:
            await (await update.message.document.get_file()).download_to_memory(out)
            out.seek(0)

            with Image.open(out) as image:
                image.thumbnail((64, 64))
                image = image.convert("RGB")

                if matrix_process is not None:
                    matrix_process.kill()
                matrix_process = Process(target=show_image, args=(image,))
                matrix_process.start()

    if message_type == "attachment_video":
        if update.message.document and update.message.document.file_size > 1000000000:
            logger.error(
                f"Too big file: {update.message.document.file_name} {update.message.document.file_size/1000}MB"
            )

        with io.BytesIO() as out:
            await (await update.message.document.get_file()).download_to_memory(out)
            out.seek(0)

            with tempfile.NamedTemporaryFile() as tempf, tempfile.NamedTemporaryFile() as tempf2:
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

    # if file_type == "photo" else await update.message.effective_attachment.get_file()
    # path = new_file.download()

    # file_extension = os.path.splitext(path)[-1]
    # print(file_extension)

    # if file_extension == ".mp4":
    #     pass
    # elif file_extension == ".tgs":
    #     with open(path) as f:
    #         lottie_object = import_tgs(f)
    #         export_gif(lottie_object, path)

    # else:
    # with io.BytesIO() as out:
    #     print(path)
    #     im.thumbnail((64, 64))
    #     im = im.convert('RGB')
    #         # im.save(path)

    #     global matrix_process
    #     if matrix_process is not None:
    #         matrix_process.kill()
    #     matrix_process = Process(target=show_image, args=(im, ))
    #     matrix_process.start()
    # todo send to matrix


# async def handle_start(update: Update, context: CallbackContext):
#     await context.bot.send_message(update.message.chat_id,
#                                    "Welcome! This is the LED matrix bot ✨🤖"
#                                    "You can send me images to show on my bright and colorful 64x64 pixel screen! "
#                                    "Larger images will be scaled down until they fit. "
#                                    "I also support GIFs and videos!")


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


if __name__ == "__main__":
    application = ApplicationBuilder().token(os.environ.get("TELEGRAM_TOKEN")).build()

    # start_handler = CommandHandler(
    #     'start', handle_start, filters.ChatType.PRIVATE & filters.TEXT)

    application.add_handler(
        MessageHandler(filters.ChatType.PRIVATE & (~filters.TEXT), handle_image)
    )
    application.add_handler(CommandHandler("skip", handle_skip))
    application.add_handler(CommandHandler("queue", handle_skip))

    try:
        application.run_polling()
    except Exception as e:
        logging.error(e)
        logging.error(traceback.format_exc())
    finally:
        matrix_process.kill()
