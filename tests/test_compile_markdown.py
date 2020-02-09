import io
from os import path

import pytest

from nikola.plugins.compile.markdown import CompileMarkdown

from .helper import FakeSite


@pytest.mark.parametrize(
    "input_str, expected_output",
    [
        pytest.param("", "", id="empty"),
        pytest.param(
            "[podcast]https://archive.org/download/Rebeldes_Stereotipos/rs20120609_1.mp3[/podcast]",
            '<p><audio controls=""><source src="https://archive.org/download/Rebeldes_Stereotipos/rs20120609_1.mp3" type="audio/mpeg"></source></audio></p>',
            id="mdx podcast",
        ),
        pytest.param(
            "~~striked out text~~",
            "<p><del>striked out text</del></p>",
            id="strikethrough",
        ),
        pytest.param(
            """\
    #!python
    from this
""",
            """\
<table class="codehilitetable"><tr><td class="linenos">\
<div class="linenodiv"><pre>1</pre></div>\
</td><td class="code"><pre class="code literal-block"><span></span>\
<code><span class="kn">from</span> <span class="nn">this</span>
</code></pre>
</td></tr></table>
""",
            id="hilite",
        ),
    ],
)
def test_compiling_markdown(
    compiler, input_path, output_path, input_str, expected_output
):
    output = markdown_compile(compiler, input_path, output_path, input_str)
    assert output.strip() == expected_output.strip()


@pytest.fixture(scope="module")
def site():
    return FakeSite()


@pytest.fixture(scope="module")
def compiler(site):
    compiler = CompileMarkdown()
    compiler.set_site(site)
    return compiler


@pytest.fixture
def input_path(tmpdir):
    return path.join(str(tmpdir), "input.markdown")


@pytest.fixture
def output_path(tmpdir):
    return path.join(str(tmpdir), "output.html")


def markdown_compile(compiler, input_path, output_path, text):
    with io.open(input_path, "w+", encoding="utf8") as input_file:
        input_file.write(text)

    compiler.compile(input_path, output_path, lang="en")

    with io.open(output_path, "r", encoding="utf8") as output_path:
        return output_path.read()
