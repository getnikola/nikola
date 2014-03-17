#!/bin/bash
cd tests/data
for i in '2.7'; do
    wget https://github.com/getnikola/invariant-builds/archive/v$i'.zip'
    unzip 'v'$i'.zip'
    rm -rf baseline$i
    mv invariant-builds-$i baseline$i
    rm 'v'$i'.zip'
done
