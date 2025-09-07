import spypoint
import requests
import datetime
import os
from urllib.parse import urlparse
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def download_new_images(url, save_path):
    try:
        # Send a GET request to the URL to download the image
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        parsed_url = urlparse(url)
        path = parsed_url.path
        filename = os.path.basename(path)

        if not filename or '.' not in filename:
            raise Exception('Photo filename missing')

        full_path = os.path.join(save_path, filename)

        # only download new images
        if os.path.exists(full_path):
            logger.warning(f"Skipping duplicate image: {full_path}")
            return

        # Open the file in binary write mode and write the content
        with open(full_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        logger.info(f"Image successfully downloaded and saved to: {full_path}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading the image: {e}")
        exit(1)
    except IOError as e:
        logger.error(f"Error saving the image: {e}")
        exit(1)


def get_photo_urls_by_camera(sp_client):
    res = {}
    cameras = sp_client.cameras()
    for cam in cameras:
        res[cam.config.name] = [p.url() for p in sp_client.photos([cam], limit=10000)]
    return res


if __name__ == "__main__":

    logger.setLevel(logging.INFO)

    # Rotate logs when file reaches 1MB, keep 5 backups
    handler = RotatingFileHandler('spypoint.log', maxBytes=1024 * 1024, backupCount=2)
    logger.addHandler(handler)

    load_dotenv(dotenv_path='.env')
    c = spypoint.Client(os.getenv('SPYPOINT_USERNAME'), os.getenv('SPYPOINT_PASSWORD'))

    photo_urls = get_photo_urls_by_camera(c)

    for cam, urls in photo_urls.items():
        cam_dir = os.path.join(os.getenv('SPYPOINT_DOWNLOAD_PATH'), cam)
        if not os.path.exists(cam_dir):
            os.makedirs(cam_dir)
            logger.info(f"Created directory: {cam_dir}")

        for url in urls:
            download_new_images(url, cam_dir)
