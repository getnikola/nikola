import argparse


def parse_args(args=None):
    parser = argparse.ArgumentParser()
    add_arguments(parser)
    options, args = parser.parse_known_args(args)
    options = process_options(options) or options
    return options, args


def add_arguments(parser):
    parser.add_argument('--conf', dest='conf_filename')
    parser.add_argument('-D', '--define', dest='defines', action='append')
    parser.add_argument('-o', '--output')


def process_options(options):
    defines = []
    for define in (options.defines or []):
        if '=' in define:
            key, _, val = define.partition('=')
        else:
            key, val = define, True
        defines.append((key, val))

    if options.output:
        defines.append(('OUTPUT_FOLDER', options.output))

    options.defines = defines
