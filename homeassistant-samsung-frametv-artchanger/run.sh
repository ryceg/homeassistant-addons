#!/usr/bin/with-contenv bashio

TVIP=$(bashio::config 'tv')
DOWNLOAD_HIGH_RES=$(bashio::config 'download_high_res')
GOOGLE_ART=$(bashio::config 'googleart')
BING_WALLPAPERS=$(bashio::config 'bing_wallpapers')
MEDIA_FOLDER=$(bashio::config 'media_folder')

mkdir -p /media/frame
echo "Using ${TVIP} as the IP of the Samsung Frame"

PARAMS=""

if bashio::config.true 'googleart'; then
    PARAMS="${PARAMS} --googleart"
fi
if bashio::config.true 'bing_wallpapers'; then
    PARAMS="${PARAMS} --bing-wallpapers"
fi
if bashio::config.true 'media_folder'; then
    PARAMS="${PARAMS} --media-folder"
fi
if bashio::config.true 'download_high_res'; then
    PARAMS="${PARAMS} --download-high-res"
fi

python3 art.py --tvip ${TVIP} ${PARAMS}

echo "done, closing now!"
kill -s SIGHUP 1
