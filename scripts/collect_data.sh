set -e

TRUSTED_TIMESTAMPING_PATH=../timestamping
WATCH_CALIBRATION_PATH=.

source config.env

# wc-collect-data $@

PATH_DATA=raw_data
PATH_DATA_NAME=$(basename $PATH_DATA)
# PATH=$PATH:$TRUSTED_TIMESTAMPING_PATH/trusted_timestamping/usr/local/bin
PATH=$PATH:/Users/sabard/dev/bil/timestamping/trustedtimestamping/usr/local/bin
# clearing any prior files
rm -f *.sha*
rm -f *.digest
rm -f tsRe*.ts*
rm -f tsCRL*.crl
rm -f timestamps*.json

echo "Hashing data directory and generating timestamp request..."
ttsGenReq $PATH_DATA
printf "Timestamp request generated\n\n"

echo "Sending timestamp request to timestamp authority servers and receiving reply..."
ttsStamp tsRequest_$PATH_DATA_NAME.tsq
printf "Timestamp replies received\n\n"

echo "Verifying timestamp replies..."
ttsVerify $PATH_DATA
printf "Verification complete\n\n"

echo "Building timestamps JSON..."
ttsPackJSON
printf "Timestamps JSON built\n\n"

echo "Deleting checksum and all timestamp reply and CRL files..."
rm *.sha*
rm *.digest
rm tsReply*.tsr
rm tsCRL*.crl
printf "Deleted\n\n"

echo "Unpacking JSON to restore checksum and all timestamp reply files..."
ttsUnpackJSON timestamps.json
printf "Unpacked\n\n"

echo "Verifying unpacked files..."
ttsVerify $PATH_DATA
printf "Verification complete\n"
