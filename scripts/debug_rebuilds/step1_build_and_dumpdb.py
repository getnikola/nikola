import dbm
import json
import subprocess
import sys


def dbm_iter(db):
    # try dictionary interface - ok in python2 and dumbdb
    try:
        return db.items()
    except Exception:
        # try firstkey/nextkey - ok for py3 dbm.gnu
        def iter_gdbm(db):
            k = db.firstkey()
            while k is not None:
                yield k, db[k]
                k = db.nextkey(k)
        return iter_gdbm(db)


def dumpdb():
    with dbm.open('.doit.db') as data:
        return {key: json.loads(value_str.decode('utf-8'))
                for key, value_str in dbm_iter(data)}


print_ = print


def print(*args, **kwargs):
    print_(*args, file=sys.stdout)
    sys.stdout.flush()


print("==> Removing stuff...")
subprocess.call(['rm', '-rf', '.doit.db', 'output', 'cache', 'cc_debug.sqlite3'])
print("==> Running first build...")
subprocess.call(['nikola', 'build'])
print("==> Fetching database...")
first = dumpdb()
print("==> Running second build...")
subprocess.call(['nikola', 'build'])
print("==> Fetching database...")
second = dumpdb()
print("==> Saving dumps...")
with open('first_dump.py', 'w', encoding='utf-8') as fh:
    fh.write(repr(first))

with open('second_dump.py', 'w', encoding='utf-8') as fh:
    fh.write(repr(second))
