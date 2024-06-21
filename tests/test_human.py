import pytest
from datetime import timedelta
from nikola.plugins.command.status import CommandStatus

@pytest.fixture(scope="module")
def command_status():
    return CommandStatus()

@pytest.mark.skip(reason="None")
def test_days_branch(command_status):
    print("\n test with 2 days 3 hours:")
    result = command_status.human_time(timedelta(days=2, hours=3))
    print(f"this is the result: ${result}")

@pytest.mark.skip(reason="None")
def test_hours_branch(command_status):
    print("test with 4 hours 20 minutes:")
    result = command_status.human_time(timedelta(hours=4, minutes=20))
    print(f"this is the result: ${result}")


@pytest.mark.skip(reason="None")
def test_minutes_branch(command_status):
    print("test with 15 minutes:")
    result = command_status.human_time(timedelta(minutes=15))
    print(f"this is the result: ${result}")

@pytest.mark.skip(reason="None")
def test_seconds_branch(command_status):
    print("test with 0 seconds:")
    result = command_status.human_time(timedelta(seconds=0))
    print(f"this is the result: ${result}")

def test_combined(command_status):
    command_status.reset_coverage()
    test_days_branch(command_status)
    test_hours_branch(command_status)
    test_minutes_branch(command_status)
    test_seconds_branch(command_status)
    command_status.report_coverage()

