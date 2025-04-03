#!/bin/bash

# provides various entry points into the watch-calibration experiment
# positional arguments:
#   {g,j,i,c,s},<image>
#   {generate-figures,jupyter,ipython,collect-data,save-image},<image>
# regenerate figures from data: ./run.sh g
# regenerate figures using container image: ./run.sh g watch-calibration.tar

# ARTS open framework config file
ENV_FILE="$(dirname $0)/config.env"

# load environment variables
source $ENV_FILE

ENGINE=docker # also tested with docker
# Containerfile
CF="$(dirname $0)/watch-calibration.cf"
if [[ $ENGINE -eq docker ]]; then
# Ignorefile (must be named .dockerignore for Docker)
  IF="$(dirname $0)/.dockerignore"
  CMD_IF=""
else
  IF="$(dirname $0)/.containerignore"
  CMD_IF="--ignorefile $IF"
fi

# positional argument variables
GENERATE_FIGURES=0
LAUNCH_JUPYTER=0
LAUNCH_IPYTHON=0
COLLECT_DATA=0
SAVE_IMAGE=0

# select function based off input argument
# defaults to generate-figures
case $1 in
  ""|g|generate-figures)
    GENERATE_FIGURES=1
    ;;
  j|jupyter)
    LAUNCH_JUPYTER=1
    ;;
  i|ipython)
    LAUNCH_IPYTHON=1
    ;;
  c|collect-data)
    COLLECT_DATA=1
    ;;
  s|save-image)
    SAVE_IMAGE=1
    ;;
  *)
    echo "Unknown option $1"
    exit 1
    ;;
esac

# load container image if supplied; otherwise build locally
if [[ -n $2 ]]; then
  $ENGINE load -i $2
else
  $ENGINE build -f $CF $CMD_IF -t watch-calibration .
fi

CONTAINER_RUN_ARGS="
    --rm -it
    --env-file $ENV_FILE
    -v $ARTS_CODE_PATH:/usr/src/exp/watch_calibration
    -v $ARTS_RAW_DATA_PATH:/usr/src/exp/raw_data
    -v $ARTS_DERIV_DATA_PATH:/usr/src/exp/deriv_data
    -v $ARTS_OUTPUT_PATH:/usr/src/exp/output
    watch-calibration
"

# generate figures
if [[ $GENERATE_FIGURES -eq 1 ]]; then
    $ENGINE run                            \
    --name watch-calibration-figures       \
    $CONTAINER_RUN_ARGS                    \
    bash -c scripts/generate_figures.sh
fi

# launch jupyter server
if [[ $LAUNCH_JUPYTER -eq 1 ]]; then
  $ENGINE run --rm -i                      \
    --name watch-calibration-jupyter       \
    -v ./notebooks:/usr/src/exp/notebooks  \
    -p 8888:8888                           \
    $CONTAINER_RUN_ARGS                    \
    bash -c scripts/launch_jupyter.sh
fi

# launch ipython kernel
if [[ $LAUNCH_IPYTHON -eq 1 ]]; then
  $ENGINE run --rm -it                    \
    --name watch-calibration-ipython      \
    $CONTAINER_RUN_ARGS                   \
    bash -c scripts/launch_ipython.sh
fi

# collect raw data using watch-calibration package
if [[ $COLLECT_DATA -eq 1 ]]; then
  $ENGINE run --rm -it                                \
    --name watch-calibration-ingest                   \
    --env-file $ENV_FILE                              \
    -v $ARTS_CODE_PATH:/usr/src/exp/watch_calibration \
    -v $ARTS_RAW_DATA_PATH:/usr/src/exp/raw_data      \
    watch-calibration                                 \
    bash -c scripts/collect_data.sh
fi

# save container image to file
if [[ $SAVE_IMAGE -eq 1 ]]; then
  $ENGINE save -o watch-calibration.tar watch-calibration
fi
