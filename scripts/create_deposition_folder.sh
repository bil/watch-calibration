REPO=$1
RAW_DATA_FOLDER=$2
DERIV_DATA_FOLDER=$3
CONTAINER_IMAGE=$4
OUTPUT_FOLDER=$5
NAME=watch_calibration.git

if [ -d "$OUTPUT_FOLDER" ]; then
    echo "OUTPUT_FOLDER exists. Remove or run with a different OUTPUT_FOLDER."
    exit
fi

git clone $REPO $OUTPUT_FOLDER
pushd $OUTPUT_FOLDER
git remote remove origin
popd

cp $CONTAINER_IMAGE $OUTPUT_FOLDER
cp -r $RAW_DATA_FOLDER $OUTPUT_FOLDER
cp -r $DERIV_DATA_FOLDER $OUTPUT_FOLDER

git clone --bare $REPO "$OUTPUT_FOLDER/watch_calibration.git"
pushd "$OUTPUT_FOLDER/watch_calibration.git"
git update-server-info
popd
