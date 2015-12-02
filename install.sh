#!/bin/bash
set -e

# This script installs the necessary dependencies for the raspberry pi wx281x
# library for powering led light strips.

sudo apt-get update && apt-get install -y \
  vim \
  tmux \
  mosh \
  build-essential \
  python-dev \
  git \
  scons \
  swig \

git clone https://github.com/jgarff/rpi_wx281x.git
cd rpi_ws281x
scons
cd python
sudo python setup.py install


