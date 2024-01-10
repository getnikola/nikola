# -*- coding: utf-8 -*-

# Copyright © 2012-2024 Chris Warrick, Roberto Alsina and others.

# Permission is hereby granted, free of charge, to any
# person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the
# Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice
# shall be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
# OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Default metadata extractors and helper functions."""

import re
from enum import Enum
from io import StringIO

import natsort

from nikola.plugin_categories import MetadataExtractor
from nikola.utils import unslugify

__all__ = ('MetaCondition', 'MetaPriority', 'MetaSource', 'check_conditions')
_default_extractors = []
DEFAULT_EXTRACTOR_NAME = 'nikola'
DEFAULT_EXTRACTOR = None


class MetaCondition(Enum):
    """Conditions for extracting metadata."""

    config_bool = 1
    config_present = 2
    extension = 3
    compiler = 4
    first_line = 5
    never = -1


class MetaPriority(Enum):
    """Priority of metadata.

    An extractor is used if and only if the higher-priority extractors returned nothing.
    """

    override = 1
    specialized = 2
    normal = 3
    fallback = 4


class MetaSource(Enum):
    """Source of metadata."""

    text = 1
    filename = 2


def check_conditions(post, filename: str, conditions: list, config: dict, source_text: str) -> bool:
    """Check the conditions for a metadata extractor."""
    for ct, arg in conditions:
        if any((
            ct == MetaCondition.config_bool and not config.get(arg, False),
            ct == MetaCondition.config_present and arg not in config,
            ct == MetaCondition.extension and not filename.endswith(arg),
            ct == MetaCondition.compiler and (post is None or post.compiler.name != arg),
            ct == MetaCondition.never
        )):
            return False
        elif ct == MetaCondition.first_line:
            if not source_text or not source_text.startswith(arg + '\n'):
                return False
    return True


def classify_extractor(extractor: MetadataExtractor, metadata_extractors_by: dict):
    """Classify an extractor and add it to the metadata_extractors_by dict."""
    global DEFAULT_EXTRACTOR
    if extractor.name == DEFAULT_EXTRACTOR_NAME:
        DEFAULT_EXTRACTOR = extractor
    metadata_extractors_by['priority'][extractor.priority].append(extractor)
    metadata_extractors_by['source'][extractor.source].append(extractor)
    metadata_extractors_by['name'][extractor.name] = extractor
    metadata_extractors_by['all'].append(extractor)


def load_defaults(site, metadata_extractors_by: dict):
    """Load default metadata extractors."""
    for extractor in _default_extractors:
        extractor.site = site
        classify_extractor(extractor, metadata_extractors_by)


def is_extractor(extractor) -> bool:  # pragma: no cover
    """Check if a given class is an extractor."""
    return isinstance(extractor, MetadataExtractor)


def default_metadata_extractors_by() -> dict:
    """Return the default metadata_extractors_by dictionary."""
    d = {
        'priority': {},
        'source': {},
        'name': {},
        'all': []
    }

    for i in MetaPriority:
        d['priority'][i] = []
    for i in MetaSource:
        d['source'][i] = []

    return d


def _register_default(extractor: type) -> type:
    """Register a default extractor."""
    _default_extractors.append(extractor())
    return extractor


@_register_default
class NikolaMetadata(MetadataExtractor):
    """Extractor for Nikola-style metadata."""

    name = 'nikola'
    source = MetaSource.text
    priority = MetaPriority.normal
    supports_write = True
    split_metadata_re = re.compile('\n\n')
    nikola_re = re.compile(r'^\s*\.\. (.*?): (.*)')
    map_from = 'nikola'  # advertised in values mapping only

    def _extract_metadata_from_text(self, source_text: str) -> dict:
        """Extract metadata from text."""
        outdict = {}
        for line in source_text.split('\n'):
            match = self.nikola_re.match(line)
            if match:
                k, v = match.group(1), match.group(2)
                if v:
                    outdict[k] = v
        return outdict

    def write_metadata(self, metadata: dict, comment_wrap=False) -> str:
        """Write metadata in this extractor’s format."""
        metadata = metadata.copy()
        order = ('title', 'slug', 'date', 'tags', 'category', 'link', 'description', 'type')
        f = '.. {0}: {1}'
        meta = []
        for k in order:
            try:
                meta.append(f.format(k, metadata.pop(k)))
            except KeyError:
                pass
        # Leftover metadata (user-specified/non-default).
        for k in natsort.natsorted(list(metadata.keys()), alg=natsort.ns.F | natsort.ns.IC):
            meta.append(f.format(k, metadata[k]))
        data = '\n'.join(meta)
        if comment_wrap is True:
            comment_wrap = ('<!--', '-->')
        if comment_wrap:
            return '\n'.join((comment_wrap[0], data, comment_wrap[1], '', ''))
        else:
            return data + '\n\n'


@_register_default
class YAMLMetadata(MetadataExtractor):
    """Extractor for YAML metadata."""

    name = 'yaml'
    source = MetaSource.text
    conditions = ((MetaCondition.first_line, '---'),)
    requirements = [('ruamel.yaml', 'ruamel.yaml', 'YAML')]
    supports_write = True
    split_metadata_re = re.compile('\n---\n')
    map_from = 'yaml'
    priority = MetaPriority.specialized

    def _extract_metadata_from_text(self, source_text: str) -> dict:
        """Extract metadata from text."""
        from ruamel.yaml import YAML
        yaml = YAML(typ='safe')
        meta = yaml.load(source_text[4:])
        # We expect empty metadata to be '', not None
        for k in meta:
            if meta[k] is None:
                meta[k] = ''
        return meta

    def write_metadata(self, metadata: dict, comment_wrap=False) -> str:
        """Write metadata in this extractor’s format."""
        from ruamel.yaml import YAML
        yaml = YAML(typ='safe')
        yaml.default_flow_style = False
        stream = StringIO()
        yaml.dump(metadata, stream)
        stream.seek(0)
        return '\n'.join(('---', stream.read().strip(), '---', ''))


@_register_default
class TOMLMetadata(MetadataExtractor):
    """Extractor for TOML metadata."""

    name = 'toml'
    source = MetaSource.text
    conditions = ((MetaCondition.first_line, '+++'),)
    requirements = [('toml', 'toml', 'TOML')]
    supports_write = True
    split_metadata_re = re.compile('\n\\+\\+\\+\n')
    map_from = 'toml'
    priority = MetaPriority.specialized

    def _extract_metadata_from_text(self, source_text: str) -> dict:
        """Extract metadata from text."""
        import toml
        return toml.loads(source_text[4:])

    def write_metadata(self, metadata: dict, comment_wrap=False) -> str:
        """Write metadata in this extractor’s format."""
        import toml
        return '\n'.join(('+++', toml.dumps(metadata).strip(), '+++', ''))


@_register_default
class FilenameRegexMetadata(MetadataExtractor):
    """Extractor for filename metadata."""

    name = 'filename_regex'
    source = MetaSource.filename
    priority = MetaPriority.fallback
    conditions = [(MetaCondition.config_bool, 'FILE_METADATA_REGEXP')]

    def _extract_metadata_from_text(self, source_text: str) -> dict:
        """Extract metadata from text."""
        # This extractor does not use the source text, and as such, this method returns an empty dict.
        return {}

    def extract_filename(self, filename: str, lang: str) -> dict:
        """Try to read the metadata from the filename based on the given re.

        This requires to use symbolic group names in the pattern.
        The part to read the metadata from the filename based on a regular
        expression is taken from Pelican - pelican/readers.py
        """
        match = re.match(self.site.config['FILE_METADATA_REGEXP'], filename)
        meta = {}

        if match:
            for key, value in match.groupdict().items():
                k = key.lower().strip()  # metadata must be lowercase
                if k == 'title' and self.site.config['FILE_METADATA_UNSLUGIFY_TITLES']:
                    meta[k] = unslugify(value, lang, discard_numbers=False)
                else:
                    meta[k] = value

        return meta
