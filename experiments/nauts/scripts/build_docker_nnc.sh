#!/bin/bash
set -e
export CONDA_ENV_NAME=mypy311

# install dependancies like tunip, tweak
pip install -r requirements.txt

# ready to conda environment for container
rm ${CONDA_ENV_NAME}.tar.gz
conda pack -n $CONDA_ENV_NAME

# build docker image for dashi-nnc
docker build -f Dockerfile.nnc --network host -t dashi-nnc:$(git describe --tags --abbrev=0) ./

