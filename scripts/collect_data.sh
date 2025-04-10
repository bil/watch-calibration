#!/bin/bash

set -e

# make ARTS environment variables available to python
set -a && . "$(dirname $0)/../config.env" && set +a

# collect data using watch-calibration package
OUTPUT=$(wc-collect-data $@)

set -- $OUTPUT
DATA_FOLDER=$1
DATA_NAME=$2

if [ ! -n $DATA_FOLDER ] && [ ! -n $DATA_NAME ]; then
  echo "Error on dataset creation"
  exit
fi

"$(dirname $0)/timestamp.sh" $DATA_NAME $DATA_FOLDER
