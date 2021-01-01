To debug unexpected Nikola rebuilds:

1. In `nikola.utils.config_changed._calc_digest`, uncomment the line that says `self._write_into_debug_db(digest, data)`
2. Create a copy of your site source.
3. Run `python step1_build_and_dumpdb.py`. (It will delete cache/output/db, build the site twice, and write dumpdb to .py files)
4. Run `python step2_analyze_py_files.py | tee analysis.txt`. It will compare the two .py files, using `cc_debug.sqlite3` and `{first,second}_dump.py`.
5. Compare the produced dictionaries. Note that you will probably need a character-level diff tool, <https://prettydiff.com/> is pretty good as long as you change CSS for `li.replace` to `word-break: break-all; white-space: pre-wrap;`

Copyright © 2019-2021, Chris Warrick.
Portions Copyright © Eduardo Nafuel Schettino and Doit Contributors.
License of .py files is MIT (same as Nikola)
