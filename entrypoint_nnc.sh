#!/bin/bash

# export PATH=/opt/conda/bin:$PATH
export PATH=${NAUTS_HOME}/dashi-env/bin:/opt/conda/bin:${PATH}

# set -euo pipefail

echo $PATH
exec uvicorn dashi.nn_clustering.runner:app --host 0.0.0.0 --port 31018
