from dalle2 import Dalle2
from varenv import *
import logging

logger = logging.getLogger("dalle_api")

try:
    dalle = Dalle2(API_Key)
except Exception as e:
    logger.critical("Failed to create DALL-E API.", exc_info=True)
    raise e


def generate_and_download_image(prompt):
    generations = dalle.generate_and_download(prompt=prompt, image_dir="tmp")
    # Çıktıyı kontrol ettikten sonra silinip silinmeyeceğini karar verilecek.
    logger.info(generations)
    logger.info("Images created and downloaded.")
