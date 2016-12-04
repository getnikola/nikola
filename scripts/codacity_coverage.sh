#!/bin/bash
PYVER=$(scripts/getpyver.py short)
if [[ $PYVER == '3.5' ]]; then
    coverage xml
    python-codacy-coverage -r coverage.xml
fi
