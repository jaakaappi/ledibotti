import logging
import os
import io

from PIL import Image
from dotenv import load_dotenv
# from lottie.exporters.gif import export_gif
# from lottie.importers.core import import_tgs
from telegram import Update, Message
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackContext, CommandHandler
from multiprocessing import Process

from showimage import show_image

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

required_env_vars = [
    "TELEGRAM_TOKEN",
]
matrix_process: Process = None

for env_var in required_env_vars:
    if env_var not in os.environ or os.environ[env_var] == "":
        raise Exception(f"Missing env var {env_var}")


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


async def handle_image(update: Update, context: CallbackContext):
    print(update.message)

    if update.message.document.file_size > 1000000000:
        logger.error(f"Too big file: {update.message.document.file_name} {update.message.document.file_size/1000}MB")

    # file_type = get_image_file_type(update.message)
    # print(file_type)

    # new_file = await update.message.effective_attachment[-1].get_file()

    with io.BytesIO() as out:
        await (await update.message.document.get_file()).download_to_memory(out)
        out.seek(0)

        with Image.open(out) as image:
            image.thumbnail((64, 64))
            image = image.convert('RGB')

            global matrix_process
            if matrix_process is not None:
                matrix_process.kill()
            matrix_process = Process(target=show_image, args=(image, ))
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


if __name__ == '__main__':
    application = ApplicationBuilder().token(
        os.environ.get("TELEGRAM_TOKEN")).build()

    image_handler = MessageHandler(
        filters.ChatType.PRIVATE & (~filters.TEXT), handle_image)
    # start_handler = CommandHandler(
    #     'start', handle_start, filters.ChatType.PRIVATE & filters.TEXT)

    application.add_handler(image_handler)
    # application.add_handler(start_handler)

    application.run_polling()
