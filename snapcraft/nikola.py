#!/snap/nikola/current/usr/bin/python3
# EASY-INSTALL-ENTRY-SCRIPT: 'Nikola==7.8.2'
__requires__ = 'Nikola==7.8.2'
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.exit(
        load_entry_point('Nikola', 'console_scripts', 'nikola')()
    )
