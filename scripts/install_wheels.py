#!/usr/bin/env python
# A workaround around idiocy of some.
import glob
import subprocess
import sys
import shlex

globres = glob.glob(str(sys.argv[1]))
subprocess.check_call(['wheel', 'install'] + globres)
