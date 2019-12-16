"""
Various integration tests for the Nikola commands.

Each test provides a different build fixture that will create a build
in the desired way that then later can be checked in test functions.

The build fixtures are scoped for module level in order to avoid
re-building the whole site for every test and to make these tests fast.
"""
