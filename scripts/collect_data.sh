#!/bin/bash

set -e

# make ARTS environment variables available to python
set -a && . "$(dirname $0)/../config.env" && set +a

# collect data using watch-calibration package
read -r DATA_FOLDER DATA_NAME <<< $(wc-collect-data $@)

"$(dirname $0)/timestamp.sh" $DATA_NAME $DATA_FOLDER
