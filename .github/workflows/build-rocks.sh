#! /usr/bin/env bash -x

# Create kfp-operators-rocks directory
[ -d ~/kfp-operators-rocks ] || mkdir ~/kfp-operators-rocks

# Loop through directories to build the rock
for d in ./*; do
    if [ -f "rockcraft.yaml" ]; then
        cd d
        rockcraft pack -v
        mv *./rock ~/kfp-operators-rocks
        cd -
    fi
done
