#!/bin/bash

if [ -e ssjson-ext.oxt ]; then
    echo 'remove ssjson-ext.oxt'
    rm ssjson-ext.oxt
fi

cd ./extension
zip -r ../ssjson-ext.oxt *
