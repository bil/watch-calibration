#!/bin/bash

set -e

IA_DEPOSITION_NAME="2504-watch-calibration-raw-data"

curl -LOs https://archive.org/download/ia-pex/ia
chmod +x ia

./ia download $IA_DEPOSITION_NAME -g "raw_data/*" --no-directories --source original
