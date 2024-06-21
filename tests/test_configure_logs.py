from nikola.log import configure_logging, print_coverage_configure, reset_coverage_configure, LoggingMode
from unittest.mock import patch
import pytest

@pytest.mark.skip(reason="None")
def test_normal_mode_debug():
    #reset_coverage_configure()
    with patch('nikola.log.DEBUG', True):
        configure_logging(logging_mode=LoggingMode.NORMAL)
        #print_coverage_configure()
        
@pytest.mark.skip(reason="None")
def test_normal_mode_no_debug():
    #reset_coverage_configure()
    configure_logging(logging_mode=LoggingMode.NORMAL)
    #print_coverage_configure()

@pytest.mark.skip(reason="None")
def test_quiet_mode_debug():
    #reset_coverage_configure()
    with patch('nikola.log.DEBUG', True):
        configure_logging(logging_mode=LoggingMode.QUIET)
        #print_coverage_configure()
  
@pytest.mark.skip(reason="None")
def test_quiet_mode_no_debug():
    #reset_coverage_configure()
    configure_logging(logging_mode=LoggingMode.QUIET)
    #print_coverage_configure()

@pytest.mark.skip(reason="None")
def test_strict_mode_debug():
    #reset_coverage_configure()
    with patch('nikola.log.DEBUG', True):
        configure_logging(logging_mode=LoggingMode.STRICT)
        #print_coverage_configure()

@pytest.mark.skip(reason="None")
def test_strict_mode_no_debug():
    #reset_coverage_configure()
    configure_logging(logging_mode=LoggingMode.STRICT)
    #print_coverage_configure()
    
    
def test_combined(command_status):
    reset_coverage_configure()
    test_normal_mode_debug()
    test_normal_mode_no_debug()
    test_quiet_mode_debug()
    test_quiet_mode_no_debug()
    test_strict_mode_debug()
    test_strict_mode_no_debug
    print_coverage_configure()

