import tweepy
from credential import *
from dalle_api import generate_and_download_image
import logging
import time
import re
import os
import sys

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
        logger.info("Twitter API created.")
    except Exception as e:
        logger.critical("Failed to create Twitter API.", exc_info=True)
        raise e
    return api


def delete_old_media():
    try:
        for image in os.listdir('./tmp'):
            if (image != '.gitkeep'):
                os.remove('./tmp/' + image)
        logger.info("Old media cleaned.")
    except Exception as e:
        logger.critical(f'Failed to clean images. Raise: {e}', exc_info=True)
        pass


def upload_media(api):
    media_ids = []
    for image in os.listdir('./tmp'):
        if (image.endswith('.png') or image.endswith('.jpg') or image.endswith('.jpeg')):
            media = api.media_upload('./tmp/' + image)
            media_ids.append(media.media_id)
    logger.info("Media uploaded.")

    return media_ids


def pre_quoted_tweet(api, tweet):
    tweet_url = f'https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}'

    for quote_tweet in tweepy.Cursor(api.search_tweets, q="url:"+tweet_url, result_type='recent').items():
        if quote_tweet.is_quote_status == True: # if the tweet is a quote
            if tweet.id == quote_tweet.quoted_status_id:    # Checks if tweet is a retweet of the specific tweet
                if api.verify_credentials().id == quote_tweet.user.id:  # Checks if the tweet is from the bot
                    logger.info(
                        f'Found a pre-quote tweet. Tweet URL: https://twitter.com/{quote_tweet.user.screen_name}/status/{quote_tweet.id}')
                    return True


def check_mentions(api, since_id):
    logger.info("Retrieving mentions...")
    new_since_id = since_id

    for tweet in tweepy.Cursor(api.mentions_timeline, since_id=since_id).items():  # Checks for new mentions
        new_since_id = max(tweet.id, new_since_id)

        if tweet.in_reply_to_status_id is not None:
            continue
        if any(re.findall(r'"([^"]*)"', tweet.text)):   # Checks if the tweet contains a quote
            logger.info(f'Found a tweet with a quote. Tweet URL: https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}')

            try:
                if pre_quoted_tweet(api, tweet):    # Checks if the tweet is a pre-quote
                    continue
            except Exception as e:
                logger.critical(f'Failed to process tweet. Raise: {e}', exc_info=True)
                pass

            try:
                prompt = re.findall(r'"([^"]*)"', tweet.text)   # Gets the quote
                generate_and_download_image(prompt[0])    # Generates an image
            except Exception as e:
                logger.critical(
                    f'Error on DALL-E image generate. Raise: {e}', exc_info=True)
                pass

            try:
                api.create_favorite(tweet.id)   # Likes the tweet
                logger.info("Tweet liked.")
            except Exception as e:
                logger.error(f'Error on like. Raise: {e}', exc_info=True)
                pass

            try:
                media_ids = upload_media(api)   # Uploads the image
            except Exception as e:
                logger.critical(
                    f'Error on upload media. Raise: {e}', exc_info=True)
                continue

            try:
                api.update_status(
                    status=f'Here is DALL·E\'s interpretation of "{prompt[0]}".',
                    attachment_url=f'https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}',
                    media_ids=media_ids)  # Replies to the tweet with the image
                logger.info("Tweet sent.")
            except Exception as e:
                logger.error(f'Error on reply. Raise: {e}', exc_info=True)
                pass

            delete_old_media()  # Deletes the image

    return new_since_id


def main():
    api = create_api()
    since_id = 1

    delete_old_media()

    while True:
        since_id = check_mentions(api, since_id)
        logger.info("Waiting...")
        time.sleep(30)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:  # Stops the program with Ctrl+C
        logger.info("Keyboard Interrupt. Cleaning...")
        delete_old_media()
        logger.info("Keyboard Interrupt. Exiting...")
        sys.exit("Keyboard Interrupt. Exiting...")
