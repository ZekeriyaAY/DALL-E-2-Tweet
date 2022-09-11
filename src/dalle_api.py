from dalle2 import Dalle2
from credential import *
import logging

logger = logging.getLogger("dalle_api")

try:
    dalle = Dalle2(API_Key)
    logger.info("DALL-E 2 API created.")
except Exception as e:
    logger.critical("Failed to create DALL-E 2 API.", exc_info=True)
    raise e


def generate_and_download_image(prompt):
    generations = dalle.generate_and_download(prompt=prompt, image_dir="images")
    logger.info(generations)   # Returns a list of image paths
    if generations is None:
        raise Exception("Failed to generate image. None!")
    logger.info("Images created and downloaded.")
