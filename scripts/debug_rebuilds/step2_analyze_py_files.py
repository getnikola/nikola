import sqlite3
import sys
print_ = print


def print(*args, **kwargs):
    print_(*args, file=sys.stdout)
    sys.stdout.flush()


with open('first_dump.py', 'r', encoding='utf-8') as fh:
    first = eval(fh.read())

with open('second_dump.py', 'r', encoding='utf-8') as fh:
    second = eval(fh.read())

if len(first) != len(second):
    print(" [!] Databases differ in size.")
    for k in first:
        if k not in second:
            print("    Item", k, "not found in second database.")
    for k in second:
        if k not in first:
            print("    Item", k, "not found in first database.")

conn = sqlite3.connect("cc_debug.sqlite3")


def get_from_db(value):
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT json_data FROM hashes WHERE hash = ?", (value,))
        return cursor.fetchone()[0]
    except Exception:
        print(" [!] Cannot find", value, "in database.")
        return None


if first == second:
    print("==> Both files are identical.")
    exit(0)

VAL_KEY = '_values_:'  # yes, ends with a colon
for k in first:
    fk, sk = first[k], second[k]
    try:
        first_values, second_values = fk[VAL_KEY], sk[VAL_KEY]
    except KeyError:
        print(" [!] Values not found for,", k)
        continue

    if first_values != second_values:
        print(" -> Difference:", k)
        for vk in first_values:
            fv, sv = first_values[vk], second_values[vk]
            if fv != sv:
                print("    first :", fv, get_from_db(fv))
                print("    second:", sv, get_from_db(sv))
