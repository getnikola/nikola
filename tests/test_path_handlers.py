"""Test that CATEGORIES_INDEX_PATH and TAGS_INDEX_PATH return the correct values on Unix and Windows."""
from unittest import mock

from nikola import Nikola
from nikola.plugins.misc.taxonomies_classifier import TaxonomiesClassifier
from nikola.plugins.task.authors import ClassifyAuthors
from nikola.plugins.task.categories import ClassifyCategories
from nikola.plugins.task.tags import ClassifyTags
from nikola.plugins.task.taxonomies import RenderTaxonomies

import pytest


@pytest.fixture(params=[ClassifyAuthors, ClassifyCategories, ClassifyTags], ids=["authors", "categories", "tags"])
def taxonomy(request):
    return request.param()


@pytest.fixture(params=[
    "base:", "base:blog", "base:path/with/trailing/slash/", "base:/path/with/leading/slash",
    "index:tags.html", "index:blog/tags.html", "index:path/to/tags.html", "index:/path/with/leading/slash.html",
])
def path(request):
    return request.param


@pytest.fixture
def fixture(taxonomy, path):
    scheme, _, path = path.partition(':')
    append_index = scheme == 'base'
    if isinstance(taxonomy, ClassifyAuthors) and append_index:
        site = Nikola(TRANSLATIONS={"en": ""}, AUTHOR_PATH=path)
    elif isinstance(taxonomy, ClassifyAuthors) and not append_index:
        pytest.skip("There is no AUTHORS_INDEX_PATH setting")
    elif isinstance(taxonomy, ClassifyCategories) and append_index:
        site = Nikola(TRANSLATIONS={"en": ""}, CATEGORY_PATH=path)
    elif isinstance(taxonomy, ClassifyCategories) and not append_index:
        site = Nikola(TRANSLATIONS={"en": ""}, CATEGORIES_INDEX_PATH=path)
    elif isinstance(taxonomy, ClassifyTags) and append_index:
        site = Nikola(TRANSLATIONS={"en": ""}, TAG_PATH=path)
    elif isinstance(taxonomy, ClassifyTags) and not append_index:
        site = Nikola(TRANSLATIONS={"en": ""}, TAGS_INDEX_PATH=path)
    else:
        raise TypeError("Unknown taxonomy %r" % type(taxonomy))

    site._template_system = mock.MagicMock()
    site._template_system.template_deps.return_value = []
    site._template_system.name = "dummy"
    site.hierarchy_per_classification = {taxonomy.classification_name: {"en": []}}
    site.posts_per_classification = {taxonomy.classification_name: {"en": {}}}
    site.taxonomy_plugins = {taxonomy.classification_name: taxonomy}

    taxonomy.set_site(site)

    classifier = TaxonomiesClassifier()
    classifier.set_site(site)

    expected = path.strip("/")
    if append_index:
        expected += "/"
    if not expected.startswith("/"):
        expected = "/" + expected

    return site, classifier, taxonomy, append_index, expected


def test_render_taxonomies_permalink(fixture):
    # Arrange
    site, _, taxonomy, _, expected = fixture
    renderer = RenderTaxonomies()
    renderer.set_site(site)

    # Act
    tasks = list(renderer._generate_classification_overview(taxonomy, "en"))

    # Assert
    action, args = tasks[0]["actions"][0]
    context = args[2]
    assert context["permalink"] == expected


def test_taxonomy_index_path_helper(fixture):
    # Arrange
    site, _, taxonomy, _, expected = fixture

    # Act
    path = site.path(taxonomy.classification_name + "_index", "name", "en", is_link=True)

    # Assert
    assert path == expected


def test_taxonomy_classifier_index_path(fixture):
    # Arrange
    site, classifier, taxonomy, append_index, expected = fixture
    if append_index:
        expected += "index.html"

    # Act
    path = classifier._taxonomy_index_path("name", "en", taxonomy)

    # Assert
    assert path == [x for x in expected.split('/') if x]


def test_taxonomy_overview_path(fixture):
    # Arrange
    _, _, taxonomy, append_index, expected = fixture

    # Act
    result = taxonomy.get_overview_path("en")

    # Assert
    assert result == ([x for x in expected.split('/') if x], "always" if append_index else "never")
