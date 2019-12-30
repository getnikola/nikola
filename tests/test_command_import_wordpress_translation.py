import os

import pytest

from nikola.plugins.command.import_wordpress import (
    modernize_qtranslate_tags,
    separate_qtranslate_tagged_langs,
)


def legacy_qtranslate_separate(text):
    """This method helps keeping the legacy tests covering various
    corner cases, but plugged on the newer methods."""
    text_bytes = text.encode("utf-8")
    modern_bytes = modernize_qtranslate_tags(text_bytes)
    modern_text = modern_bytes.decode("utf-8")
    return separate_qtranslate_tagged_langs(modern_text)


@pytest.mark.parametrize(
    "content, french_translation, english_translation",
    [
        pytest.param("[:fr]Voila voila[:en]BLA[:]", "Voila voila", "BLA", id="simple"),
        pytest.param(
            "[:fr]Voila voila[:]COMMON[:en]BLA[:]",
            "Voila voila COMMON",
            "COMMON BLA",
            id="pre modern with intermission",
        ),
        pytest.param(
            "<!--:fr-->Voila voila<!--:-->COMMON<!--:en-->BLA<!--:-->",
            "Voila voila COMMON",
            "COMMON BLA",
            id="withintermission",
        ),
        pytest.param(
            "<!--:fr-->Voila voila<!--:-->COMMON<!--:fr-->MOUF<!--:--><!--:en-->BLA<!--:-->",
            "Voila voila COMMON MOUF",
            "COMMON BLA",
            id="with uneven repartition",
        ),
        pytest.param(
            "<!--:fr-->Voila voila<!--:--><!--:en-->BLA<!--:-->COMMON<!--:fr-->MOUF<!--:-->",
            "Voila voila COMMON MOUF",
            "BLA COMMON",
            id="with uneven repartition bis",
        ),
    ],
)
def test_legacy_split_a_two_language_post(
    content, french_translation, english_translation
):
    content_translations = legacy_qtranslate_separate(content)
    assert french_translation == content_translations["fr"]
    assert english_translation == content_translations["en"]


def test_conserves_qtranslate_less_post():
    content = """Si vous préférez savoir à qui vous parlez commencez par visiter l'<a title="À propos" href="http://some.blog/about/">À propos</a>.

Quoiqu'il en soit, commentaires, questions et suggestions sont les bienvenues !"""
    content_translations = legacy_qtranslate_separate(content)
    assert 1 == len(content_translations)
    assert content == content_translations[""]


def test_modernize_a_wordpress_export_xml_chunk(test_dir):
    raw_export_path = os.path.join(
        test_dir, "data", "wordpress_import", "wordpress_qtranslate_item_raw_export.xml"
    )
    with open(raw_export_path, "rb") as raw_xml_chunk_file:
        content = raw_xml_chunk_file.read()

    output = modernize_qtranslate_tags(content)

    modernized_xml_path = os.path.join(
        test_dir, "data", "wordpress_import", "wordpress_qtranslate_item_modernized.xml"
    )
    with open(modernized_xml_path, "rb") as modernized_chunk_file:
        expected = modernized_chunk_file.read()

    assert expected == output


def test_modernize_qtranslate_tags():
    content = b"<!--:fr-->Voila voila<!--:-->COMMON<!--:fr-->MOUF<!--:--><!--:en-->BLA<!--:-->"
    output = modernize_qtranslate_tags(content)
    assert b"[:fr]Voila voila[:]COMMON[:fr]MOUF[:][:en]BLA[:]" == output


def test_split_a_two_language_post():
    content = """<!--:fr-->Si vous préférez savoir à qui vous parlez commencez par visiter l'<a title="À propos" href="http://some.blog/about/">À propos</a>.

Quoiqu'il en soit, commentaires, questions et suggestions sont les bienvenues !
<!--:--><!--:en-->If you'd like to know who you're talking to, please visit the <a title="À propos" href="http://some.blog/about/">about page</a>.

Comments, questions and suggestions are welcome !
<!--:-->"""
    content_translations = legacy_qtranslate_separate(content)

    assert (
        content_translations["fr"] == """Si vous préférez savoir à qui vous parlez commencez par visiter l'<a title="À propos" href="http://some.blog/about/">À propos</a>.

Quoiqu'il en soit, commentaires, questions et suggestions sont les bienvenues !
"""
    )

    assert (
        content_translations["en"] == """If you'd like to know who you're talking to, please visit the <a title="À propos" href="http://some.blog/about/">about page</a>.

Comments, questions and suggestions are welcome !
"""
    )


def test_split_a_two_language_post_with_teaser():
    content = """<!--:fr-->Si vous préférez savoir à qui vous parlez commencez par visiter l'<a title="À propos" href="http://some.blog/about/">À propos</a>.

Quoiqu'il en soit, commentaires, questions et suggestions sont les bienvenues !
<!--:--><!--:en-->If you'd like to know who you're talking to, please visit the <a title="À propos" href="http://some.blog/about/">about page</a>.

Comments, questions and suggestions are welcome !
<!--:--><!--more--><!--:fr-->
Plus de détails ici !
<!--:--><!--:en-->
More details here !
<!--:-->"""
    content_translations = legacy_qtranslate_separate(content)
    assert (
        content_translations["fr"] == """Si vous préférez savoir à qui vous parlez commencez par visiter l'<a title="À propos" href="http://some.blog/about/">À propos</a>.

Quoiqu'il en soit, commentaires, questions et suggestions sont les bienvenues !
 <!--more--> \n\
Plus de détails ici !
"""
    )
    assert (
        content_translations["en"] == """If you'd like to know who you're talking to, please visit the <a title="À propos" href="http://some.blog/about/">about page</a>.

Comments, questions and suggestions are welcome !
 <!--more--> \n\
More details here !
"""
    )
