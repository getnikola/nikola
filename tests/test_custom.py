"""
Simple custom tests.

More advanced tests should be in a separate module.
"""


def test_color_formatter():
    "Test the ColorfulFormatter class."
    import logging
    from nikola.log import ColorfulFormatter
    
    formatter = ColorfulFormatter()
    # Test cases for each logging level and the colorful toggle
    test_cases = [
        (logging.INFO, False), (logging.INFO, True),
        (logging.WARNING, False), (logging.WARNING, True),
        (logging.ERROR, False), (logging.ERROR, True)
    ]

    for level, colorState in test_cases:
        # Create a LogRecord for the current level
        log_record = logging.LogRecord(
            name="test",
            level=level,
            pathname=__file__,
            lineno=10,
            msg="Test message",
            args=None,
            exc_info=None
        )

        formatter._colorful = colorState

        # Call wrap_in_color and print the result for verification
        formatted_message = formatter.format(log_record)
        print(f"Level: {log_record.levelname}, Colorful: {colorState}, Output: {formatted_message}")

