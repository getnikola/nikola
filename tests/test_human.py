import pytest
from datetime import timedelta
from nikola.plugins.command.status import CommandStatus 

@pytest.fixture(scope="module")
def command_status():
    return CommandStatus()


def test_days_branch(command_status):
    command_status.reset_coverage()
    result = command_status.human_time(timedelta(days=2, hours=3))
    print(result)
    command_status.report_coverage()

def test_hours_branch(command_status):
    command_status.reset_coverage()
    result = command_status.human_time(timedelta(hours=4, minutes=20))
    print(result)
    command_status.report_coverage()

def test_minutes_branch(command_status):
    command_status.reset_coverage()
    result = command_status.human_time(timedelta(minutes=15))
    print(result)
    command_status.report_coverage()

def test_seconds_branch(command_status):
    command_status.reset_coverage()
    result = command_status.human_time(timedelta(seconds=0))
    print(result)
    command_status.report_coverage()


