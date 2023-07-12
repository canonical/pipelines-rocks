#!/usr/bin/env bash
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

set -x

for FILE in ~/kfp-operators-rocks/; do
    ROCK_NAME=$(basename ${FILE} .rock)
    sudo skopeo --insecure-policy copy oci-archive:${FILE} docker-daemon:${ROCK_NAME}:v0-test
    docker save ${ROCK_NAME} > ${ROCK_NAME}.tar
    microk8s ctr image import ${ROCK_NAME}.tar --digests=true
done
