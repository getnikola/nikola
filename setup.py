#!/usr/bin/env python

from distutils.core import setup

setup(name='Nikola',
      version='3.1',
      description='Static blog/website generator',
      author='Roberto Alsina and others',
      author_email='ralsina@netmanagers.com.ar',
      url='http://nikola.ralsina.com.ar/',
      packages=['nikola'],
      data_files=[('samplesite', 'data/samplesite'),
                  ('themes', 'data/themes')],
      scripts=['scripts/nikola'],
     )