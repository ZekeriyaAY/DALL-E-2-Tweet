import tweepy
from varenv import *
from dalle_api import generate_and_download_image
import logging
import time
import re


logger = logging.getLogger("twitter_api")
logging.basicConfig(filename='./log/log1.log',
                    filemode='w', level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
logger.setLevel(level=logging.INFO)
logger.info("Logging started.")


def create_api():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True)

    try:
        api.verify_credentials()
        logger.info("API created.")
    except Exception as e:
        logger.critical("Failed to create API.", exc_info=True)
        raise e
    return api


def delete_old_media():
    for image in os.listdir('./tmp'):
        if (image != '.gitkeep'):
            os.remove('./tmp/' + image)
    logger.info("Old media cleaned.")


def upload_media(api):
    media_ids = []
    for image in os.listdir('./tmp'):
        if (image.endswith('.png') or image.endswith('.jpg') or image.endswith('.jpeg')):
            media = api.media_upload('./tmp/' + image)
            media_ids.append(media.media_id)
    logger.info("Media uploaded.")

    return media_ids


def check_mentions(api, since_id):
    logger.info("Retrieving mentions...")
    new_since_id = since_id

    for tweet in tweepy.Cursor(api.mentions_timeline,
                               since_id=since_id).items():
        new_since_id = max(tweet.id, new_since_id)

        if tweet.in_reply_to_status_id is not None:
            continue
        if any(re.findall(r'"([^"]*)"', tweet.text)):
            logger.info(
                f'Found a tweet with a quote. Tweet URL: https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}')

            try:
                delete_old_media()
            except Exception as e:
                logger.critical("Failed to clean images.", exc_info=True)
                pass

            try:
                prompt = re.findall(r'"([^"]*)"', tweet.text)
                generate_and_download_image(prompt[0])
            except Exception as e:
                logger.critical(
                    f'Error on DALL-E image generate. Raise: {e}', exc_info=True)
                pass

            try:
                api.create_favorite(tweet.id)
                logger.info("Tweet liked.")
            except Exception as e:
                logger.error(f'Error on like. Raise: {e}', exc_info=True)
                pass

            try:
                media_ids = upload_media(api)
            except Exception as e:
                logger.critical(
                    f'Error on upload media. Raise: {e}', exc_info=True)
                continue

            try:
                api.update_status(
                    status=f'Here is DALL-E\'s interpretation of "{prompt[0]}".',
                    attachment_url=f'https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}',
                    media_ids=media_ids
                )
                logger.info("Tweet sent.")
            except Exception as e:
                logger.error(f'Error on reply. Raise: {e}', exc_info=True)
                pass

    return new_since_id


def main():
    api = create_api()
    since_id = 1

    while True:
        since_id = check_mentions(api, since_id)
        logger.info("Waiting...")
        time.sleep(30)


if __name__ == '__main__':
    main()
