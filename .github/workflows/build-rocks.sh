#!/usr/bin/env bash
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

set -x

ROCKS_DIR=$1
CURRENT_TIME=$(date "+%Y.%m.%d-%H.%M.%S")

# Create kfp-operators-rocks directory
[ -d ~/kfp-operators-rocks ] || mkdir ~/kfp-operators-rocks

# Build the rock from a file or the root of this repo
if [ -f "${ROCKS_DIR}/rockcraft.yaml" ]; then
    cd ${ROCKS_DIR}
    rockcraft pack -v
    mv *.rock ~/kfp-operators-rocks/"${ROCKS_DIR}-built-at-${CURRENT_TIME}.rock"
    cd -
else 
    for d in ${ROCKS_DIR}/*; do
        if [ -f "${d}/rockcraft.yaml" ]; then
            cd ${d}
            rockcraft pack -v
            mv *.rock ~/kfp-operators-rocks/
            cd -
        fi
    done
fi
