#!/bin/bash

# trusted timestamping variables
TTS_PATH="$(dirname $0)/../tts"

# TTS_REPO=https://github.com/bil/timestamping
TTS_REPO="https://github.com/sabard/timestamping --branch sabard/darwin"
DATA_NAME=$1
DATA_PATH=$2
if [[ "$DIR" = /* ]]; then
  RAW_DATA_DIR=$ARTS_RAW_DATA_PATH
else
  RAW_DATA_DIR="../$ARTS_RAW_DATA_PATH"
fi
PATH=$PATH:timestamping/trustedtimestamping/usr/local/bin

pushd $TTS_PATH

# clone timestamping repo if nonexistent
if [ ! -d timestamping ]; then
  git clone $TTS_REPO timestamping
fi

# clear prior files
rm -f *.sha*
rm -f *.digest
rm -f tsRe*.ts*
rm -f tsCRL*.crl
rm -f timestamps*.json
rm -f tsVerify.json

echo "Hashing data directory and generating timestamp request..."
ttsGenReq $DATA_PATH
printf "Timestamp request generated\n\n"

echo "Sending timestamp request to timestamp authority servers and receiving reply..."
ttsStamp tsRequest_$DATA_NAME.tsq
printf "Timestamp replies received\n\n"

echo "Verifying timestamp replies..."
ttsVerify $DATA_PATH
printf "Verification complete\n\n"

echo "Building timestamps JSON..."
ttsPackJSON
mv timestamps.json $RAW_DATA_DIR/timestamps_$DATA_NAME.json
printf "Timestamps JSON built\n\n"

echo "Deleting checksum and all timestamp reply and CRL files..."
rm *.sha*
rm *.digest
rm tsReply*.tsr
rm tsCRL*.crl
printf "Deleted\n\n"

echo "Unpacking JSON to restore checksum and all timestamp reply files..."
ttsUnpackJSON $RAW_DATA_DIR/timestamps_$DATA_NAME.json
printf "Unpacked\n\n"

echo "Verifying unpacked files..."
ttsVerify $DATA_PATH
printf "Verification complete\n"

popd $TTS_PATH
