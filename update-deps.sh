#!/bin/sh

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

pyenv activate watch-calibration

pip install --upgrade setuptools pip
pip install wheel pip-tools

pip-compile "$@"
pip-sync requirements.txt
pip install -e file:.#egg=watch_calibration
