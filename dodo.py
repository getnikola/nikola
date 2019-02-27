
import os
import fnmatch

DOIT_CONFIG = {
    'default_tasks': ['flake8', 'test'],
    'reporter': 'executed-only',
}


def recursive_glob(path, pattern):
    """recursively walk path directories and return files matching the pattern"""
    for root, dirnames, filenames in os.walk(path, followlinks=True):
        for filename in fnmatch.filter(filenames, pattern):
            yield os.path.join(root, filename)


def task_flake8():
    """flake8 - static check for python files"""
    yield {
        'name': os.path.join(os.getcwd(), 'nikola'),
        'actions': ['flake8 nikola/'],
    }


def task_pydocstyle():
    """pydocstyle -- static check for docstring style"""
    yield {
        'name': os.path.join(os.getcwd(), 'nikola'),
        'actions': ["pydocstyle --count --match-dir='(?!^\\.)(?!data).*' nikola/"],
    }


def task_test():
    """run unit-tests using py.test"""
    return {
        'actions': ['py.test tests/'],
    }


def task_coverage():
    """run unit-tests using py.test, with coverage reporting"""
    return {
        'actions': ['py.test --cov nikola --cov-report term-missing tests/'],
        'verbosity': 2,
    }


def task_gen_completion():
    """generate tab-completion scripts"""
    cmd = 'nikola tabcompletion --shell {0} --hardcode-tasks > _nikola_{0}'
    for shell in ('bash', 'zsh'):
        yield {
            'name': shell,
            'actions': [cmd.format(shell)],
            'targets': ['_nikola_{0}'.format(shell)],
        }
