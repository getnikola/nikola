#!/bin/bash
cd tests/data
for i in $@; do
    if [[ $i == '2.7' ]]; then
        # we only support 2.7 now
        echo 'Version '$i' does not have baseline testing.'
        wget https://github.com/getnikola/invariant-builds/archive/v$i'.zip'
        unzip 'v'$i'.zip'
        rm -rf baseline$i
        mv invariant-builds-$i baseline$i
        rm 'v'$i'.zip'
    fi
done
