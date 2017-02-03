#!/bin/bash
PYVER=$(scripts/getpyver.py short)
if [[ $PYVER == '3.6' ]]; then
    coverage xml
    python-codacy-coverage -r coverage.xml
fi
