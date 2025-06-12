# gcloud auth login
# set project

ENGINE=podman
IMAGE_URL=us-docker.pkg.dev/soe-bil-cd/bil/watch-calibration
ENV_VARS=$(sed '/^#/d' config.env | sed '/^[[:space:]]*$/d' | paste -s -d, /dev/stdin)

REGION=us-west1

# $ENGINE tag watch-calibration $IMAGE_URL
# $ENGINE push $IMAGE_URL

gcloud run deploy watch-calibration --image=$IMAGE_URL --port=8888 --set-env-vars $ENV_VARS --region us-west1
