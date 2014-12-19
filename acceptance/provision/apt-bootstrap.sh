#!/bin/bash

STAGE=/var/cache/apt/vm-created
if [ ! -f $STAGE ]; then
    apt-get update
    touch $STAGE
else
    if [[ $(( $(date +%s) - $(stat -c %Z /var/cache/apt/pkgcache.bin) )) -gt $(( 24 * 60 * 60 * 7)) ]]; then
        apt-get update
    fi
fi
