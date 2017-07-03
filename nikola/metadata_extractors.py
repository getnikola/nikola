# -*- coding: utf-8 -*-

# Copyright © 2012-2017 Roberto Alsina, Chris Warrick and others.

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
from nikola.plugin_categories import MetadataExtractor
from nikola.utils import unslugify, req_missing

__all__ = ('MetaCondition', 'MetaPriority', 'MetaSource', 'check_conditions')
me_defaults = ('NikolaMetadata', 'YAMLMetadata', 'TOMLMetadata', 'FilenameRegexMetadata')
DEFAULT_EXTRACTOR_NAME = 'nikola'
DEFAULT_EXTRACTOR = None


class MetaCondition(Enum):
    """Conditions for extracting metadata."""

    config_bool = 1
    extension = 2
    compiler = 3
    first_line = 4
    never = -1


class MetaPriority(Enum):
    """Priority of metadata.

    An extractor is used if and only if the higher-priority extractors returned nothing."""

    specialized = 1
    normal = 2
    fallback = 3


class MetaSource(Enum):
    """Source of metadata."""

    text = 1
    filename = 2


def check_conditions(post, filename: str, conditions: list, config: dict, source_text: str):
    """Check the conditions for a metadata extractor."""
    for ct, arg in conditions:
        if any((
            ct == MetaCondition.config_bool and not config[arg],
            ct == MetaCondition.extension and not filename.endswith(arg),
            ct == MetaCondition.compiler and post.compiler.name != arg,
            ct == MetaCondition.never
        )):
            return False
        elif ct == MetaCondition.first_line:
            if not source_text or not source_text.startswith(arg + '\n'):
                return False
    return True


def check_requirements(extractor: MetadataExtractor):
    """Check if requirements for an extractor are passed. This is called if conditions are met."""
    for import_name, pip_name, friendly_name in extractor.requirements:
        try:
            __import__(import_name)
        except ImportError:
            req_missing([pip_name], "use {0} metadata".format(friendly_name), python=True, optional=False)


def is_extractor(extractor):
    """Check if a given class is an extractor."""
    return isinstance(extractor, MetadataExtractor)

class NikolaMetadata(MetadataExtractor):
    """Extractor for Nikola-style metadata."""

    name = 'nikola'
    source = MetaSource.text
    priority = MetaPriority.normal
    split_metadata_re = re.compile('\n\n')
    nikola_re = re.compile('^\.\. (.*?): (.*)')

    def _extract_metadata_from_text(self, source_text: str) -> dict:
        # TODO: what was `match` for in old re_meta thing for?
        outdict = {}
        for line in source_text.split('\n'):
            match = self.nikola_re.match(line)
            if match:
                outdict[match.group(1)] = match.group(2)
        return outdict


class YAMLMetadata(MetadataExtractor):
    """Extractor for YAML metadata."""

    name = 'yaml'
    source = MetaSource.text
    conditions = ((MetaCondition.first_line, '---'),)
    requirements = [('yaml', 'PyYAML', 'YAML')]
    split_metadata_re = re.compile('\n---\n')
    map_from = 'yaml'
    priority = MetaPriority.specialized

    def _extract_metadata_from_text(self, source_text: str) -> dict:
        import yaml
        meta = yaml.safe_load(source_text[4:])
        # We expect empty metadata to be '', not None
        for k in meta:
            if meta[k] is None:
                meta[k] = ''
        return meta


class TOMLMetadata(MetadataExtractor):
    """Extractor for TOML metadata."""

    name = 'toml'
    source = MetaSource.text
    conditions = ((MetaCondition.first_line, '+++'),)
    requirements = [('toml', 'toml', 'TOML')]
    split_metadata_re = re.compile('\n\\+\\+\\+\n')
    map_from = 'toml'
    priority = MetaPriority.specialized

    def _extract_metadata_from_text(self, source_text: str) -> dict:
        import toml
        return toml.loads(source_text[4:])


class FilenameRegexMetadata(MetadataExtractor):
    """Extractor for filename metadata."""

    name = 'filename_regex'
    source = MetaSource.filename
    priority = MetaPriority.fallback
    conditions = [(MetaCondition.config_bool, 'FILE_METADATA_REGEXP')]

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
