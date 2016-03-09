#!/usr/bin/env python3
import subprocess
import os
import argparse

if not os.path.exists('.pypt/gh-token'):
    print("To use this script, you must create a GitHub token first.")
    print("Get a token here: https://github.com/settings/tokens")
    print("Then, put it in a file named .pypt/gh-token")
    exit(1)

parser = argparse.ArgumentParser(description="GitHub Release helper")
parser.add_argument("FILE", nargs=1, help="Markdown file to use")
parser.add_argument("TAG", nargs=1, help="Tag name (usually vX.Y.Z)")

args = parser.parse_args()

if not args.TAG[0].startswith("v"):
    print("WARNING: tag should start with v")
    i = input("Add `v` to tag? [y/n] ")
    if i.lower().strip().startswith('y'):
        args.TAG[0] = 'v' + args.TAG[0]

BASEDIR = os.getcwd()
REPO = 'getnikola/nikola'

subprocess.call(['.pypt/ghrel', args.FILE[0], BASEDIR, REPO, args.TAG[0]])
