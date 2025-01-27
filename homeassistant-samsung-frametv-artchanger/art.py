import sys
import logging
import os
import json
import argparse
from io import BytesIO
import random

sys.path.append('../')

from samsungtvws import SamsungTVWS
from sources.google_art import get_google_art_image
from sources.bing_wallpapers import get_bing_wallpaper
from sources.utils import resize_and_crop_image
from sources.media_folder import process_media_folder_images, get_remote_filename

# Add command line argument parsing
parser = argparse.ArgumentParser(description='Upload images to Samsung TV.')
parser.add_argument('--upload-all', action='store_true', help='Upload all images at once')
parser.add_argument('--debug', action='store_true', help='Enable debug mode to check if TV is reachable')
parser.add_argument('--tvip', help='IP address of the Samsung the Frame')
parser.add_argument('--googleart', action='store_true', help='Download and upload image from Google Arts & Culture')
parser.add_argument('--download-high-res', action='store_true', help='Download high resolution image using dezoomify-rs')
parser.add_argument('--bing-wallpapers', action='store_true', help='Download and upload image from Bing Wallpapers')
parser.add_argument('--media-folder', action='store_true', help='Use images from the local media folder')
parser.add_argument('--debugimage', action='store_true', help='Save downloaded and resized images for inspection')

args = parser.parse_args()

# Set the path to the folder containing the images
folder_path = 'frame'

# Set the path to the file that will store the list of uploaded filenames
upload_list_path = 'uploaded_files.json'

# Load the list of uploaded filenames from the file
if os.path.isfile(upload_list_path):
    with open(upload_list_path, 'r') as f:
        uploaded_files = json.load(f)
else:
    uploaded_files = []

# Increase debug level
logging.basicConfig(level=logging.INFO)

tvip = args.tvip
# Set your TVs local IP address. Highly recommend using a static IP address for your TV.
tv = SamsungTVWS(tvip)

# Check if TV is reachable in debug mode
if args.debug:
    try:
        logging.info('Checking if the TV can be reached.')
        info = tv.rest_device_info()
        logging.info('If you do not see an error, your TV could be reached.')
        sys.exit()
    except Exception as e:
        logging.error('Could not reach the TV: ' + str(e))
        sys.exit()

def save_debug_image(image_data, filename):
    if args.debugimage:
        with open(filename, 'wb') as f:
            f.write(image_data.getvalue())
        logging.info(f'Debug image saved as {filename}')

# Checks if the TV supports art mode
art_mode = tv.art().supported()

if art_mode == True:
    # Retrieve information about the currently selected art
    current_art = tv.art().get_current()

    enabled_sources = []
    if args.bing_wallpapers:
        enabled_sources.append('bing_wallpapers')
    if args.googleart:
        enabled_sources.append('googleart')
    if args.media_folder:
        enabled_sources.append('media_folder')

    if not enabled_sources:
        logging.error('No image source specified. Please use --googleart, --bing-wallpapers, or --media-folder')
        sys.exit()

    selected_source = random.choice(enabled_sources)
    logging.info(f'Selected source: {selected_source}')

    if selected_source == 'bing_wallpapers':
        logging.info('Fetching image from Bing Wallpapers...')
        image_data, file_type, date = get_bing_wallpaper()
        if image_data is None:
            sys.exit()

        save_debug_image(image_data, f'debug_bing_original_{date}.jpg')

        logging.info('Resizing and cropping the Bing Wallpaper image...')
        resized_image_data = resize_and_crop_image(image_data)

        save_debug_image(resized_image_data, f'debug_bing_resized_{date}.jpg')

        image_data = resized_image_data
        remote_filename = None
    elif selected_source == 'googleart':
        logging.info('Fetching image from Google Arts & Culture...')
        image_data, file_type, image_info = get_google_art_image(args.download_high_res)
        if image_data is None:
            sys.exit()

        save_debug_image(image_data, f'debug_googleart_original_{image_info}.jpg')

        logging.info('Resizing and cropping the Google Arts & Culture image...')
        resized_image_data = resize_and_crop_image(image_data)

        save_debug_image(resized_image_data, f'debug_googleart_resized_{image_info}.jpg')

        image_data = resized_image_data
        remote_filename = None
    elif selected_source == 'media_folder':
        image_data, file_type, file = process_media_folder_images(folder_path, uploaded_files, args.upload_all)
        if image_data is None:
            sys.exit()

        save_debug_image(image_data, f'debug_custom_original_{os.path.basename(file)}')

        logging.info('Resizing and cropping the image...')
        resized_image_data = resize_and_crop_image(image_data)

        save_debug_image(resized_image_data, f'debug_custom_resized_{os.path.basename(file)}')

        image_data = resized_image_data
        remote_filename = get_remote_filename(file, uploaded_files)

    if remote_filename is None:
        try:
            logging.info(f'Uploading image')
            remote_filename = tv.art().upload(image_data.getvalue(), file_type=file_type, matte="none")
            tv.art().select_image(remote_filename, show=True)
            logging.info(f'Image uploaded and selected')

            if args.media_folder:
                # Add the filename to the list of uploaded filenames
                uploaded_files.append({'file': file, 'remote_filename': remote_filename})
                # Save the list of uploaded filenames to the file
                with open(upload_list_path, 'w') as f:
                    json.dump(uploaded_files, f)
        except Exception as e:
            logging.error(f'There was an error uploading the image: ' + str(e))
            sys.exit()
    else:
        if not args.upload_all:
            # Select the image using the remote file name only if not in 'upload-all' mode
            logging.info('Setting existing image, skipping upload')
            tv.art().select_image(remote_filename, show=True)

else:
    logging.warning('Your TV does not support art mode.')
