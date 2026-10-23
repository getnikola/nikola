#!/usr/bin/python

import sys


def hello(name='world'):
    greeting = "hello " + name
    print(greeting)


if __name__ == "__main__":
    hello(*sys.argv[1:])
