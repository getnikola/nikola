#!/usr/bin/python

import sys


def hello(name='world'):
    print "hello", name

if __name__ == "__main__":
    hello(*sys.argv[1:])
