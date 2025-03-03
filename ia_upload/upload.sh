#!/bin/bash

# TODO get default values from ia.ini
IA_CFG_FILE=~/.config/internetarchive/ia.ini
# access:  cat $IA_CFG_FILE | grep access | awk '{print $3}'
# secret:  cat $IA_CFG_FILE | grep secret | awk '{print $3}'
S3_ACCESS=${S3_ACCESS:-""}
S3_SECRET=${S3_SECRET:-""}

if ! command -v ./ia &> /dev/null; then
    curl -LOs https://archive.org/download/ia-pex/ia
    chmod +x ia
fi

if [[ -n $S3_ACCESS ]] && [[ -n $S3_SECRET ]]; then
    # create ia.ini file
    # if [ -f $IA_CFG_FILE ]; then
    #     rm $IA_CFG_FILE
    # fi
    mkdir -p ~/.config/internetarchive
    echo "[s3]" > $IA_CFG_FILE
    echo "access = $S3_ACCESS" >> $IA_CFG_FILE
    echo "secret = $S3_SECRET" >> $IA_CFG_FILE
else
    ./ia configure
fi

./ia upload --spreadsheet=metadata.csv

