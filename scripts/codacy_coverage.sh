#!/bin/bash
PYVER=$(scripts/getpyver.py short)
if [[ $PYVER == '3.6' ]]; then
    if [[ "x$CODACY_PROJECT_TOKEN" == "x" ]]; then
        echo "Warning: Codacy token not available (PR from non-member), unable to send coverage info."
        exit 0
    fi
    coverage xml
    python-codacy-coverage -r coverage.xml
fi
