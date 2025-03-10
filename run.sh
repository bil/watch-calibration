# Containers

source "$(dirname $0 )/config.env"

ENGINE=podman
CF="$(dirname $0)/watch-calibration.cf"
# CF="$(dirname $0)/watch-calibration-alpine.cf"
IF="$(dirname $0)/.containerignore"
ENV_FILE="$(dirname $0)/config.env"

GENERATE_FIGURES=0
LAUNCH_JUPYTER=0
LAUNCH_IPYTHON=0
COLLECT_DATA=0
EXPORT_IMAGE=0

POSITIONAL_ARGS=()

# generate figures

case $1 in
  -g|--generate-figures)
    GENERATE_FIGURES=1
    shift
    ;;
  -j|--jupyter)
    LAUNCH_JUPYTER=1
    shift
    ;;
  -i|--ipython)
    LAUNCH_IPYTHON=1
    shift
    ;;
  -c|--collect-data)
    COLLECT_DATA=1
    shift
    ;;
  -e|--export-image)
    EXPORT_IMAGE=1
    shift
    ;;
  -*|--*)
    echo "Unknown option $1"
    exit 1
    ;;
  # *)
  #   POSITIONAL_ARGS+=("$1") # save positional arg
  #   shift
  #   ;;
esac

# set -- "${POSITIONAL_ARGS[@]}" # restore positional parameters

# $ENGINE build -f $CF -t watch-calibration .
$ENGINE build -f $CF --ignorefile $IF -t watch-calibration .

if [[ $GENERATE_FIGURES -eq 1 ]]; then
    $ENGINE run --rm            \
      --name watch-calibration-figures  \
      --env-file $ENV_FILE      \
      -v $ARTS_RAW_DATA_PATH:/usr/src/exp/$ARTS_RAW_DATA_PATH   \
      -v $(pwd)/figures:/figs   \
      watch-calibration         \
      bash -c "python -c 'from watch_calibration import WatchCalibration; wc = WatchCalibration(); wc.generate_figures()' ; cp /usr/src/exp/fig1.svg /usr/src/exp/fig1.html /figs"
fi

if [[ $LAUNCH_JUPYTER -eq 1 ]]; then
  # jupyter notebook --config "$(dirname $0)/notebooks/jupyter_notebook_config.py"
    $ENGINE run --rm -it        \
      --name watch-calibration-jupyter  \
      --env-file $ENV_FILE      \
      -p 8888:8888              \
      watch-calibration         \
      jupyter notebook --config /usr/src/exp/notebooks/jupyter_notebook_config.py --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''
fi

if [[ $LAUNCH_IPYTHON -eq 1 ]]; then
    $ENGINE run --rm -it     \
      --name watch-calibration-ipython \
      --env-file $ENV_FILE     \
      -v $(pwd):/figs          \
      watch-calibration        \
      ipython -c "%run watch_calibration/watch_calibration.py"
fi

if [[ $COLLECT_DATA -eq 1 ]]; then
    $ENGINE run --rm -v $(pwd):/usr/src/exp -it watch-calibration wc-collect-data $@
fi

if [[ $EXPORT_IMAGE -eq 1 ]]; then
    $ENGINE save -o watch-calibration.tar watch-calibration
fi
