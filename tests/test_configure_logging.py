from nikola.log import configure_logging, print_coverage_configure, reset_coverage_configure, LoggingMode
from unittest.mock import patch


def test_normal_mode_debug():
    reset_coverage_configure()
    with patch('nikola.log.DEBUG', True):
        configure_logging(logging_mode=LoggingMode.NORMAL)
        print_coverage_configure()
        

def test_normal_mode_no_debug():
    reset_coverage_configure()
    configure_logging(logging_mode=LoggingMode.NORMAL)
    print_coverage_configure()


def test_quiet_mode_debug():
    reset_coverage_configure()
    with patch('nikola.log.DEBUG', True):
        configure_logging(logging_mode=LoggingMode.QUIET)
        print_coverage_configure()
  
def test_quiet_mode_no_debug():
    reset_coverage_configure()
    configure_logging(logging_mode=LoggingMode.QUIET)
    print_coverage_configure()

def test_strict_mode_debug():
    reset_coverage_configure()
    with patch('nikola.log.DEBUG', True):
        configure_logging(logging_mode=LoggingMode.STRICT)
        print_coverage_configure()

def test_strict_mode_no_debug():
    reset_coverage_configure()
    configure_logging(logging_mode=LoggingMode.STRICT)
    print_coverage_configure()