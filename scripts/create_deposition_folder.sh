#!/bin/bash

set -e

REPO=$1
RAW_DATA_FOLDER=$2
DERIV_DATA_FOLDER=$3
CONTAINER_IMAGE=$4
OUTPUT_FOLDER=$5
BARE_REPO_NAME="watch-calibration.git"

if [ -d "$OUTPUT_FOLDER" ]; then
    echo "OUTPUT_FOLDER exists. Remove or run with a different OUTPUT_FOLDER."
    exit
fi

git clone $REPO $OUTPUT_FOLDER
pushd $OUTPUT_FOLDER
rm -rf .git
popd

cp $CONTAINER_IMAGE $OUTPUT_FOLDER
cp -r $RAW_DATA_FOLDER $OUTPUT_FOLDER
cp -r $DERIV_DATA_FOLDER $OUTPUT_FOLDER

git clone --bare --no-local $REPO "$OUTPUT_FOLDER/$BARE_REPO_NAME"
pushd "$OUTPUT_FOLDER/$BARE_REPO_NAME"

# necessary in the case of cloning from a local repo
git gc --aggressive --prune=now
git repack -adf

git update-server-info
popd
