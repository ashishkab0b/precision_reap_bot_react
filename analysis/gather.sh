#!/usr/bin/env bash


ROOT_DIR="/Users/ashish/files/research/projects/alexithymia/xsect_affForecast_spr22"
DATA_DIR="${ROOT_DIR}/data/"
TIMESTAMP=`date +%Y-%m-%d_%H-%M-%S`
DATESTAMP=`date +%Y-%m-%d`
RAW_DIR="${DATA_DIR}/raw/${DATESTAMP}"

mkdir ${RAW_DIR}

~/files/scripts/qualtrics_module.py responses SV_XXXXXXXXX --output_dir ${RAW_DIR}


# ROOT_DIR="/Users/ashish/files/research/data/<path>"
# DATA_DIR="${ROOT_DIR}/data/"
# TIMESTAMP=`date +%Y-%m-%d_%H-%M-%S`

# cp -ri "$DATA_DIR/data/raw" data
# cp -ri "$DATA_DIR/doc" .

# find "$DATA_DIR/data/raw" -type f -not -name .DS_Store -exec cp -ri {} ./data/raw/ \;


# echo $TIMESTAMP >> "$DATA_DIR/filecopy.log"
# echo "Copied files to:" >> "$DATA_DIR/filecopy.log"
# echo $(pwd) >> "$DATA_DIR/filecopy.log"
# echo "" >> "$DATA_DIR/filecopy.log"
