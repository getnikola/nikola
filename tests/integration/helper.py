import io
import os


def append_config(config_dir, appendix):
    config_path = os.path.join(config_dir, "conf.py")
    with io.open(config_path, "a", encoding="utf8") as outf:
        outf.write(appendix)


def patch_config(config_dir, *replacements):
    config_path = os.path.join(config_dir, "conf.py")
    with io.open(config_path, "r", encoding="utf-8") as inf:
        data = inf.read()

    for old, new in replacements:
        data = data.replace(old, new)

    with io.open(config_path, "w+", encoding="utf8") as outf:
        outf.write(data)
        outf.flush()
