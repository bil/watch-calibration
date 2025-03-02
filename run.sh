# jupyter notebook --config "$(dirname $0)/jupyter_notebook_config.py"

# Containers

ENGINE=podman
CF="$(dirname $0)/watch-calibration.cf"
# CF="$(dirname $0)/watch-calibration-alpine.cf"
IF="$(dirname $0)/.containerignore"

GENERATE_FIGURES=0
LAUNCH_JUPYTER=0
LAUNCH_IPYTHON=0
COLLECT_DATA=0
EXPORT_IMAGE=0

POSITIONAL_ARGS=()

# generate figures

while [[ $# -gt 0 ]]; do
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
    *)
      POSITIONAL_ARGS+=("$1") # save positional arg
      shift # past argument
      ;;
  esac
done

set -- "${POSITIONAL_ARGS[@]}" # restore positional parameters

$ENGINE build -f $CF --ignorefile $IF -t watch-calibration .

$ENGINE save -o watch-calibration.tar watch-calibration

if [[ $GENERATE_FIGURES -eq 1 ]]; then
    $ENGINE run --rm -v $(pwd):/figs -it watch-calibration cp /usr/src/exp/fig1.svg /usr/src/exp/fig1.html /figs
fi

if [[ $LAUNCH_JUPYTER -eq 1 ]]; then
    $ENGINE run --rm -p 8888:8888 -it watch-calibration jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root
fi

if [[ $LAUNCH_IPYTHON -eq 1 ]]; then
    $ENGINE run --rm -v $(pwd):/figs -it watch-calibration ipython
    # need to pass:  %run watch_calibration/watch_calibration.py
fi

if [[ $COLLECT_DATA -eq 1 ]]; then
    $ENGINE run --rm -v $(pwd):/usr/src/exp -it watch-calibration wc-collect-data
fi

if [[ $EXPORT_IMAGE -eq 1 ]]; then
    $ENGINE image save watch-calibration > watch-calibration.tar
fi
