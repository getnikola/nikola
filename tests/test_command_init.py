from unittest import mock

import pytest

from nikola.plugins.command.init import (
    SAMPLE_CONF,
    CommandInit,
    format_default_translations_config,
)

from .helper import cd


def test_command_init_with_defaults(
    init_command,
    ask_questions,
    copy_sample_site,
    create_configuration,
    create_empty_site,
):
    init_command.execute()

    assert ask_questions.called
    assert create_configuration.called
    assert not copy_sample_site.called
    assert create_empty_site.called


def test_command_init_with_arguments(
    init_command,
    ask_questions,
    copy_sample_site,
    create_configuration,
    create_empty_site,
):
    arguments = dict(options={"demo": True, "quiet": True}, args=["destination"])
    init_command.execute(**arguments)

    assert not ask_questions.called
    assert create_configuration.called
    assert copy_sample_site.called
    assert not create_empty_site.called


def test_init_called_without_target_quiet(
    init_command,
    ask_questions,
    copy_sample_site,
    create_configuration,
    create_empty_site,
):
    init_command.execute(**{"options": {"quiet": True}})

    assert not ask_questions.called
    assert not create_configuration.called
    assert not copy_sample_site.called
    assert not create_empty_site.called


def test_command_init_with_empty_dir(
    init_command,
    ask_questions,
    copy_sample_site,
    create_configuration,
    create_empty_site,
):
    init_command.execute(args=["destination"])

    assert ask_questions.called
    assert create_configuration.called
    assert not copy_sample_site.called
    assert create_empty_site.called


def test_configure_translations_without_additional_languages():
    """
    Testing the configuration of the translation when no additional language has been found.
    """
    translations_cfg = format_default_translations_config(set())
    assert SAMPLE_CONF["TRANSLATIONS"] == translations_cfg


def test_configure_translations_with_2_additional_languages():
    """
    Testing the configuration of the translation when two additional languages are given.
    """
    translations_cfg = format_default_translations_config(set(["es", "en"]))
    assert translations_cfg == """{
    DEFAULT_LANG: "",
    "en": "./en",
    "es": "./es",
}"""


@pytest.fixture
def init_command(
    tmpdir, ask_questions, copy_sample_site, create_configuration, create_empty_site
):
    with mock.patch(
        "nikola.plugins.command.init.CommandInit.ask_questions", ask_questions
    ):
        with mock.patch(
            "nikola.plugins.command.init.CommandInit.copy_sample_site", copy_sample_site
        ):
            with mock.patch(
                "nikola.plugins.command.init.CommandInit.create_configuration",
                create_configuration,
            ):
                with mock.patch(
                    "nikola.plugins.command.init.CommandInit.create_empty_site",
                    create_empty_site,
                ):
                    with cd(str(tmpdir)):
                        yield CommandInit()


@pytest.fixture
def ask_questions():
    return mock.MagicMock()


@pytest.fixture
def copy_sample_site():
    return mock.MagicMock()


@pytest.fixture
def create_configuration():
    return mock.MagicMock()


@pytest.fixture
def create_empty_site():
    return mock.MagicMock()
