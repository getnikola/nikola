# -*- coding: utf-8 -*-

# Copyright © 2012-2024 Roberto Alsina and others.

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

"""Nikola plugin categories."""

import io
import logging
import os
import typing

import doit
from doit.cmd_base import Command as DoitCommand

from .utils import LOGGER, first_line, get_logger, req_missing

if typing.TYPE_CHECKING:
    import nikola
    import nikola.post

__all__ = (
    'Command',
    'LateTask',
    'PageCompiler',
    'RestExtension',
    'MarkdownExtension',
    'MetadataExtractor',
    'Task',
    'TaskMultiplier',
    'TemplateSystem',
    'SignalHandler',
    'ConfigPlugin',
    'PostScanner',
    'Taxonomy',
)


class BasePlugin:
    """Base plugin class."""

    logger = None

    def set_site(self, site):
        """Set site, which is a Nikola instance."""
        self.site = site
        self.logger = get_logger(self.name)
        if not site.debug:
            self.logger.level = logging.INFO

    def set_module_path(self, module_path):
        """Set the plugin's module path."""
        self.module_path = module_path

    def inject_dependency(self, target, dependency):
        """Add 'dependency' to the target task's task_deps."""
        self.site.injected_deps[target].append(dependency)

    def get_deps(self, filename, context=None):
        """Find the dependencies for a file."""
        return []

    def register_auto_watched_folder(self, folder: str) -> None:
        self.site.registered_auto_watched_folders.add(folder)


class PostScanner(BasePlugin):
    """The scan method of these plugins is called by Nikola.scan_posts."""

    def scan(self) -> 'typing.List[nikola.post.Post]':
        """Create a list of posts from some source. Returns a list of Post objects."""
        raise NotImplementedError()

    def supported_extensions(self) -> 'typing.Optional[typing.List]':
        """Return a list of supported file extensions, or None if such a list isn't known beforehand."""
        return None


class Command(BasePlugin, DoitCommand):
    """Doit command implementation."""

    name = "dummy_command"

    doc_purpose = "A short explanation."
    doc_usage = ""
    doc_description = None  # None value will completely omit line from doc
    # see https://pydoit.org/cmd_run.html#parameters
    cmd_options = ()
    needs_config = True

    def __init__(self, *args, **kwargs):
        """Initialize a command."""
        BasePlugin.__init__(self, *args, **kwargs)
        DoitCommand.__init__(self)

    def __call__(self, config=None, **kwargs):
        """Reset doit arguments (workaround)."""
        self._doitargs = kwargs
        DoitCommand.__init__(self, config, **kwargs)
        return self

    def execute(self, options=None, args=None) -> int:
        """Check if the command can run in the current environment, fail if needed, or call _execute."""
        options = options or {}
        args = args or []

        if self.needs_config and not self.site.configured:
            LOGGER.error("This command needs to run inside an existing Nikola site.")
            return False
        return self._execute(options, args)

    def _execute(self, options, args) -> int:
        """Do whatever this command does.

        @param options (dict) with values from cmd_options
        @param args (list) list of positional arguments
        """
        raise NotImplementedError()


def help(self):
    """Return help text for a command."""
    text = []
    text.append("Purpose: %s" % self.doc_purpose)
    text.append("Usage:   nikola %s %s" % (self.name, self.doc_usage))
    text.append('')

    text.append("Options:")
    for opt in self.cmdparser.options:
        text.extend(opt.help_doc())

    if self.doc_description is not None:
        text.append("")
        text.append("Description:")
        text.append(self.doc_description)
    return "\n".join(text)


# we need to patch DoitCommand.help with doit <0.31.0
if doit.__version__ < (0, 31, 0):
    DoitCommand.help = help


class BaseTask(BasePlugin):
    """Base for task generators."""

    name = "dummy_task"

    # default tasks are executed by default.
    # the others have to be specifie in the command line.
    is_default = True

    def gen_tasks(self) -> 'typing.List[dict]':
        """Generate tasks."""
        raise NotImplementedError()

    def group_task(self) -> dict:
        """Return dict for group task."""
        return {
            'basename': self.name,
            'name': None,
            'doc': first_line(self.__doc__),
        }


class Task(BaseTask):
    """Task generator."""

    name = "dummy_task"


class LateTask(BaseTask):
    """Late task generator (plugin executed after all Task plugins)."""

    name = "dummy_latetask"


class TemplateSystem(BasePlugin):
    """Provide support for templating systems."""

    name = "dummy_templates"

    def set_directories(self, directories: 'typing.List[str]', cache_folder: str):
        """Set the list of folders where templates are located and cache."""
        raise NotImplementedError()

    def template_deps(self, template_name: str, context=None):
        """Return filenames which are dependencies for a template."""
        raise NotImplementedError()

    def get_deps(self, filename: str, context=None):
        """Return paths to dependencies for the template loaded from filename."""
        raise NotImplementedError()

    def get_string_deps(self, text: str, context=None):
        """Find dependencies for a template string."""
        raise NotImplementedError()

    def render_template(self, template_name: str, output_name: str, context: 'typing.Dict[str, str]'):
        """Render template to a file using context.

        This must save the data to output_name *and* return it
        so that the caller may do additional processing.
        """
        raise NotImplementedError()

    def render_template_to_string(self, template: str, context: 'typing.Dict[str, str]') -> str:
        """Render template to a string using context."""
        raise NotImplementedError()

    def inject_directory(self, directory: str):
        """Inject the directory with the lowest priority in the template search mechanism."""
        raise NotImplementedError()

    def get_template_path(self, template_name: str) -> str:
        """Get the path to a template or return None."""
        raise NotImplementedError()


class TaskMultiplier(BasePlugin):
    """Take a task and return *more* tasks."""

    name = "dummy multiplier"

    def process(self, task) -> list:
        """Examine task and create more tasks. Returns extra tasks only."""
        return []


class PageCompiler(BasePlugin):
    """Compile text files into HTML."""

    name = "dummy_compiler"
    friendly_name = ''
    demote_headers = False
    supports_onefile = True
    use_dep_file = True  # If set to false, the .dep file is never written and not automatically added as a target
    supports_metadata = False
    metadata_conditions = []
    default_metadata = {
        'title': '',
        'slug': '',
        'date': '',
        'tags': '',
        'category': '',
        'link': '',
        'description': '',
        'type': 'text',
    }
    config_dependencies = []

    def get_dep_filename(self, post: 'nikola.post.Post', lang: str) -> str:
        """Return the .dep file's name for the given post and language."""
        return post.translated_base_path(lang) + '.dep'

    def _read_extra_deps(self, post: 'nikola.post.Post', lang: str) -> 'typing.List[str]':
        """Read contents of .dep file and return them as a list."""
        dep_path = self.get_dep_filename(post, lang)
        if os.path.isfile(dep_path):
            with io.open(dep_path, 'r+', encoding='utf-8-sig') as depf:
                deps = [l.strip() for l in depf.readlines()]
                return deps
        return []

    def register_extra_dependencies(self, post: 'nikola.post.Post'):
        """Add dependency to post object to check .dep file."""
        def create_lambda(lang: str) -> 'typing.Callable':
            # We create a lambda like this so we can pass `lang` to it, because if we didn’t
            # add that function, `lang` would always be the last language in TRANSLATIONS.
            # (See https://docs.python-guide.org/writing/gotchas/#late-binding-closures)
            return lambda: self._read_extra_deps(post, lang)

        for lang in self.site.config['TRANSLATIONS']:
            post.add_dependency(create_lambda(lang), 'fragment', lang=lang)

    def get_extra_targets(self, post: 'nikola.post.Post', lang: str, dest: str) -> 'typing.List[str]':
        """Return a list of extra targets for the render_posts task when compiling the post for the specified language."""
        if self.use_dep_file:
            return [self.get_dep_filename(post, lang)]
        else:
            return []

    def compile(self, source: str, dest: str, is_two_file=True, post=None, lang=None):
        """Compile the source file into HTML and save as dest."""
        raise NotImplementedError()

    def compile_string(self, data: str, source_path=None, is_two_file=True, post=None, lang=None) -> str:
        """Compile the source file into HTML strings (with shortcode support).

        Returns a tuple of at least two elements: HTML string [0] and shortcode dependencies [last].
        """
        # This function used to have some different APIs in different places.
        raise NotImplementedError()

    def create_post(self, path: str, content=None, onefile=False, is_page=False, **kw):
        """Create post file with optional metadata."""
        raise NotImplementedError()

    def extension(self) -> str:
        """Return the preferred extension for the output of this compiler."""
        return ".html"

    def read_metadata(self, post: 'nikola.post.Post', lang=None) -> 'typing.Dict[str, str]':
        """Read the metadata from a post, and return a metadata dict."""
        return {}

    def split_metadata(self, data: str, post=None, lang=None) -> (str, str):
        """Split data from metadata in the raw post content."""
        if lang and post:
            extractor = post.used_extractor[lang]
        else:
            import nikola.metadata_extractors
            extractor = nikola.metadata_extractors.DEFAULT_EXTRACTOR

        if isinstance(extractor, MetadataExtractor):
            return extractor.split_metadata_from_text(data)
        # Ouch!
        return data, data

    def get_compiler_extensions(self) -> list:
        """Activate all the compiler extension plugins for a given compiler and return them."""
        plugins = []
        for plugin_info in self.site.compiler_extensions:
            if plugin_info.compiler == self.name or plugin_info.plugin_object.compiler_name == self.name:
                plugins.append(plugin_info)
        return plugins


class CompilerExtension(BasePlugin):
    """An extension for a Nikola compiler.

    If you intend to implement those in your own compiler, you can:
    (a) create a new plugin class for them; or
    (b) use this class and filter them yourself.
    If you choose (b), you should the compiler name to the .plugin
    file in the Nikola/compiler section and filter all plugins of
    this category, getting the compiler name with `plugin_info.compiler`.
    """

    name = "dummy_compiler_extension"
    compiler_name = "dummy_compiler"


class RestExtension(CompilerExtension):
    """Extensions for reStructuredText."""

    name = "dummy_rest_extension"
    compiler_name = "rest"


class MarkdownExtension(CompilerExtension):
    """Extensions for Markdown."""

    name = "dummy_markdown_extension"
    compiler_name = "markdown"


class MetadataExtractor(BasePlugin):
    """Plugins that can extract meta information from post files."""

    # Name of the extractor. (required)
    name = "unknown"
    # Where to get metadata from. (MetaSource; required)
    source = None
    # Priority of extractor. (MetaPriority; required)
    priority = None
    # List of tuples (MetaCondition, arg) with conditions used to select this extractor.
    conditions = []
    # Regular expression used for splitting metadata, or None if not applicable.
    split_metadata_re = None
    # List of tuples (import name, pip name, friendly name) of Python packages required for this extractor.
    requirements = []
    # Name of METADATA_MAPPING to use, if any.
    map_from = None
    # Whether or not the extractor supports writing metadata.
    supports_write = False

    def _extract_metadata_from_text(self, source_text: str) -> 'typing.Dict[str, str]':
        """Extract metadata from text."""
        raise NotImplementedError()

    def split_metadata_from_text(self, source_text: str) -> (str, str):
        """Split text into metadata and content (both strings)."""
        if self.split_metadata_re is None:
            return source_text
        else:
            split_result = self.split_metadata_re.split(source_text.lstrip(), maxsplit=1)
            if len(split_result) == 1:
                return split_result[0], split_result[0]
            else:
                # Necessary?
                return split_result[0], split_result[-1]

    def extract_text(self, source_text: str) -> 'typing.Dict[str, str]':
        """Split file, return metadata and the content."""
        split = self.split_metadata_from_text(source_text)
        if not split:
            return {}
        meta = self._extract_metadata_from_text(split[0])
        return meta

    def extract_filename(self, filename: str, lang: str) -> 'typing.Dict[str, str]':
        """Extract metadata from filename."""
        return {}

    def write_metadata(self, metadata: 'typing.Dict[str, str]', comment_wrap=False) -> str:
        """Write metadata in this extractor’s format.

        ``comment_wrap`` is either True, False, or a 2-tuple of comments to use for wrapping, if necessary.
        If it’s set to True, defaulting to  ``('<!--', '-->')`` is recommended.

        This function should insert comment markers (if applicable) and must insert trailing newlines.
        """
        raise NotImplementedError()

    def check_requirements(self):
        """Check if requirements for an extractor are satisfied."""
        for import_name, pip_name, friendly_name in self.requirements:
            try:
                __import__(import_name)
            except ImportError:
                req_missing([pip_name], "use {0} metadata".format(friendly_name), python=True, optional=False)


class SignalHandler(BasePlugin):
    """Signal handlers."""

    name = "dummy_signal_handler"


class ConfigPlugin(BasePlugin):
    """A plugin that can edit config (or modify the site) on-the-fly."""

    name = "dummy_config_plugin"


class CommentSystem(BasePlugin):
    """A plugn that offers a new comment system."""

    name = "dummy_comment_system"


class ShortcodePlugin(BasePlugin):
    """A plugin that adds a shortcode."""

    name = "dummy_shortcode_plugin"

    def set_site(self, site):
        """Set Nikola site."""
        self.site = site
        site.register_shortcode(self.name, self.handler)
        return super().set_site(site)


class Importer(Command):
    """Basic structure for importing data into Nikola.

    The flow is:

    read_data
    preprocess_data
    parse_data
    generate_base_site
        populate_context
        create_config
    filter_data
    process_data

    process_data can branch into:

    import_story (may use import_file and save_post)
    import_post (may use import_file and save_post)
    import_attachment (may use import_file)

    Finally:

    write_urlmap
    """

    name = "dummy_importer"

    def _execute(self, options={}, args=[]):
        """Import the data into Nikola."""
        raise NotImplementedError()

    def generate_base_site(self, path: str):
        """Create the base site."""
        raise NotImplementedError()

    def populate_context(self):
        """Use data to fill context for configuration."""
        raise NotImplementedError()

    def create_config(self):
        """Use the context to create configuration."""
        raise NotImplementedError()

    def read_data(self, source):
        """Fetch data into self.data."""
        raise NotImplementedError()

    def preprocess_data(self):
        """Modify data if needed."""
        pass

    def parse_data(self):
        """Convert self.data into self.items."""
        raise NotImplementedError()

    def filter_data(self):
        """Remove data that's not to be imported."""
        pass

    def process_data(self):
        """Go through self.items and save them."""

    def import_story(self):
        """Create a page."""
        raise NotImplementedError()

    def import_post(self):
        """Create a post."""
        raise NotImplementedError()

    def import_attachment(self):
        """Create an attachment."""
        raise NotImplementedError()

    def import_file(self):
        """Import a file."""
        raise NotImplementedError()

    def save_post(self):
        """Save a post to disk."""
        raise NotImplementedError()


class Taxonomy(BasePlugin):
    """Taxonomy for posts.

    A taxonomy plugin allows to classify posts (see #2107) by
    classification strings. Classification plugins must adjust
    a set of options to determine certain aspects.

    The following options are class attributes with their default
    values. These variables should be set in the class definition,
    in the constructor or latest in the `set_site` function.

    classification_name = "taxonomy":
        The classification name to be used for path handlers.
        Must be overridden!

    overview_page_items_variable_name = "items":
        When rendering the overview page, its template will have a list
        of pairs
            (friendly_name, link)
        for the classifications available in a variable by this name.

        The template will also have a list
            (friendly_name, link, post_count)
        for the classifications available in a variable by the name
        `overview_page_items_variable_name + '_with_postcount'`.

    overview_page_variable_name = "taxonomy":
        When rendering the overview page, its template will have a list
        of classifications available in a variable by this name.

    overview_page_hierarchy_variable_name = "taxonomy_hierarchy":
        When rendering the overview page, its template will have a list
        of tuples
            (friendly_name, classification, classification_path, link,
             indent_levels, indent_change_before, indent_change_after)
        available in a variable by this name. These tuples can be used
        to render the hierarchy as a tree.

        The template will also have a list
            (friendly_name, classification, classification_path, link,
             indent_levels, indent_change_before, indent_change_after,
             number_of_children, post_count)
        available in the variable by the name
        `overview_page_hierarchy_variable_name + '_with_postcount'`.

    more_than_one_classifications_per_post = False:
        If True, there can be more than one classification per post; in that case,
        the classification data in the metadata is stored as a list. If False,
        the classification data in the metadata is stored as a string, or None
        when no classification is given.

    has_hierarchy = False:
        Whether the classification has a hierarchy.

    include_posts_from_subhierarchies = False:
        If True, the post list for a classification includes all posts with a
        sub-classification (in case has_hierarchy is True).

    include_posts_into_hierarchy_root = False:
        If True, include_posts_from_subhierarchies == True will also insert
        posts into the post list for the empty hierarchy [].

    show_list_as_subcategories_list = False:
        If True, for every classification which has at least one
        subclassification, create a list of subcategories instead of a list/index
        of posts. This is only used when has_hierarchy = True. The template
        specified in subcategories_list_template will be used. If this is set
        to True, it is recommended to set include_posts_from_subhierarchies to
        True to get correct post counts.

    show_list_as_index = False:
        Whether to show the posts for one classification as an index or
        as a post list.

    subcategories_list_template = "taxonomy_list.tmpl":
        The template to use for the subcategories list when
        show_list_as_subcategories_list is True.

    template_for_single_list = "tagindex.tmpl":
        The template to use for the post list for one classification.

    template_for_classification_overview = "list.tmpl":
        The template to use for the classification overview page.
        Set to None to avoid generating overviews.

    always_disable_atom = False:
        Whether to always disable Atom feed generation.

    always_disable_rss = False:
        Whether to always disable RSS feed generation.

    apply_to_posts = True:
        Whether this classification applies to posts.

    apply_to_pages = False:
        Whether this classification applies to pages.

    minimum_post_count_per_classification_in_overview = 1:
        The minimum number of posts a classification must have to be listed in
        the overview.

    omit_empty_classifications = False:
        Whether post lists resp. indexes should be created for empty
        classifications.

    add_other_languages_variable = False:
        In case this is `True`, each classification page will get a list
        of triples `(other_lang, other_classification, title)` of classifications
        in other languages which should be linked. The list will be stored in the
        variable `other_languages`.

    path_handler_docstrings:
        A dictionary of docstrings for path handlers. See eg. nikola.py for
        examples.  Must be overridden, keys are "taxonomy_index", "taxonomy",
        "taxonomy_atom", "taxonomy_rss" (but using classification_name instead
        of "taxonomy").  If one of the values is False, the corresponding path
        handler will not be created.
    """

    name = "dummy_taxonomy"

    # Adjust the following values in your plugin!
    classification_name = "taxonomy"
    overview_page_variable_name = "taxonomy"
    overview_page_items_variable_name = "items"
    overview_page_hierarchy_variable_name = "taxonomy_hierarchy"
    more_than_one_classifications_per_post = False
    has_hierarchy = False
    include_posts_from_subhierarchies = False
    include_posts_into_hierarchy_root = False
    show_list_as_subcategories_list = False
    show_list_as_index = False
    subcategories_list_template = "taxonomy_list.tmpl"
    template_for_single_list = "tagindex.tmpl"
    template_for_classification_overview = "list.tmpl"
    always_disable_atom = False
    always_disable_rss = False
    apply_to_posts = True
    apply_to_pages = False
    minimum_post_count_per_classification_in_overview = 1
    omit_empty_classifications = False
    add_other_languages_variable = False
    path_handler_docstrings = {
        'taxonomy_index': '',
        'taxonomy': '',
        'taxonomy_atom': '',
        'taxonomy_rss': '',
    }

    def is_enabled(self, lang=None) -> bool:
        """Return True if this taxonomy is enabled, or False otherwise.

        If lang is None, this determins whether the classification is
        made at all. If lang is not None, this determines whether the
        overview page and the classification lists are created for this
        language.
        """
        return True

    def get_implicit_classifications(self, lang: str) -> 'typing.List[str]':
        """Return a list of classification strings which should always appear in posts_per_classification."""
        return []

    def classify(self, post: 'nikola.post.Post', lang: str) -> 'typing.Iterable[str]':
        """Classify the given post for the given language.

        Must return a list or tuple of strings.
        """
        raise NotImplementedError()

    def sort_posts(self, posts: 'typing.List[nikola.post.Post]', classification: str, lang: str):
        """Sort the given list of posts.

        Allows the plugin to order the posts per classification as it wants.
        The posts will be ordered by date (latest first) before calling
        this function. This function must sort in-place.
        """
        pass

    def sort_classifications(self, classifications: 'typing.List[str]', lang: str, level=None):
        """Sort the given list of classification strings.

        Allows the plugin to order the classifications as it wants. The
        classifications will be ordered by `natsort` before calling this
        function. This function must sort in-place.

        For hierarchical taxonomies, the elements of the list are a single
        path element of the path returned by `extract_hierarchy()`. The index
        of the path element in the path will be provided in `level`.
        """
        pass

    def get_classification_friendly_name(self, classification: str, lang: str, only_last_component=False) -> str:
        """Extract a friendly name from the classification.

        The result of this function is usually displayed to the user, instead
        of using the classification string.

        The argument `only_last_component` is only relevant to hierarchical
        taxonomies. If it is set, the printable name should only describe the
        last component of `classification` if possible.
        """
        raise NotImplementedError()

    def get_overview_path(self, lang: str, dest_type='page') -> str:
        """Return path for classification overview.

        This path handler for the classification overview must return one or
        two values (in this order):
         * a list or tuple of strings: the path relative to OUTPUT_DIRECTORY;
         * a string with values 'auto', 'always' or 'never', indicating whether
           INDEX_FILE should be added or not.

        Note that this function must always return a list or tuple of strings;
        the other return value is optional with default value `'auto'`.

        In case INDEX_FILE should potentially be added, the last element in the
        returned path must have no extension, and the PRETTY_URLS config must
        be ignored by this handler. The return value will be modified based on
        the PRETTY_URLS and INDEX_FILE settings.

        `dest_type` can be either 'page', 'feed' (for Atom feed) or 'rss'.
        """
        raise NotImplementedError()

    def get_path(self, classification: str, lang: str, dest_type='page') -> str:
        """Return path to the classification page.

        This path handler for the given classification must return one to
        three values (in this order):
         * a list or tuple of strings: the path relative to OUTPUT_DIRECTORY;
         * a string with values 'auto', 'always' or 'never', indicating whether
           INDEX_FILE should be added or not;
         * an integer if a specific page of the index is to be targeted (will be
           ignored for post lists), or `None` if the most current page is targeted.

        Note that this function must always return a list or tuple of strings;
        the other two return values are optional with default values `'auto'` and
        `None`.

        In case INDEX_FILE should potentially be added, the last element in the
        returned path must have no extension, and the PRETTY_URLS config must
        be ignored by this handler. The return value will be modified based on
        the PRETTY_URLS and INDEX_FILE settings.

        `dest_type` can be either 'page', 'feed' (for Atom feed) or 'rss'.

        For hierarchical taxonomies, the result of extract_hierarchy is provided
        as `classification`. For non-hierarchical taxonomies, the classification
        string itself is provided as `classification`.
        """
        raise NotImplementedError()

    def extract_hierarchy(self, classification: str) -> 'typing.List[str]':
        """Given a classification, return a list of parts in the hierarchy.

        For non-hierarchical taxonomies, it usually suffices to return
        `[classification]`.
        """
        return [classification]

    def recombine_classification_from_hierarchy(self, hierarchy: 'typing.List[str]') -> str:
        """Given a list of parts in the hierarchy, return the classification string.

        For non-hierarchical taxonomies, it usually suffices to return hierarchy[0].
        """
        return hierarchy[0]

    def provide_overview_context_and_uptodate(self, lang: str) -> str:
        """Provide data for the context and the uptodate list for the classification overview.

        Must return a tuple of two dicts. The first is merged into the page's context,
        the second will be put into the uptodate list of all generated tasks.

        Context must contain `title`.
        """
        raise NotImplementedError()

    def provide_context_and_uptodate(self, classification: str, lang: str, node=None) -> 'typing.Tuple[typing.Dict]':
        """Provide data for the context and the uptodate list for the list of the given classification.

        Must return a tuple of two dicts. The first is merged into the page's context,
        the second will be put into the uptodate list of all generated tasks.

        For hierarchical taxonomies, node is the `hierarchy_utils.TreeNode` element
        corresponding to the classification.

        Context must contain `title`, which should be something like 'Posts about <classification>'.
        """
        raise NotImplementedError()

    def should_generate_classification_page(self, classification: str, post_list: 'typing.List[nikola.post.Post]', lang: str) -> bool:
        """Only generates list of posts for classification if this function returns True."""
        return True

    def should_generate_atom_for_classification_page(self, classification: str, post_list: 'typing.List[nikola.post.Post]', lang: str) -> bool:
        """Only generates Atom feed for list of posts for classification if this function returns True."""
        return self.should_generate_classification_page(classification, post_list, lang)

    def should_generate_rss_for_classification_page(self, classification: str, post_list: 'typing.List[nikola.post.Post]', lang: str) -> bool:
        """Only generates RSS feed for list of posts for classification if this function returns True."""
        return self.should_generate_classification_page(classification, post_list, lang)

    def postprocess_posts_per_classification(self, posts_per_classification_per_language: 'typing.List[nikola.post.Post]', flat_hierarchy_per_lang=None, hierarchy_lookup_per_lang=None) -> 'typing.List[nikola.post.Post]':
        """Rearrange, modify or otherwise use the list of posts per classification and per language.

        For compatibility reasons, the list could be stored somewhere else as well.

        In case `has_hierarchy` is `True`, `flat_hierarchy_per_lang` is the flat
        hierarchy consisting of `hierarchy_utils.TreeNode` elements, and
        `hierarchy_lookup_per_lang` is the corresponding hierarchy lookup mapping
        classification strings to `hierarchy_utils.TreeNode` objects.
        """
        pass

    def get_other_language_variants(self, classification: str, lang: str, classifications_per_language: 'typing.List[str]') -> 'typing.List[str]':
        """Return a list of variants of the same classification in other languages.

        Given a `classification` in a language `lang`, return a list of pairs
        `(other_lang, other_classification)` with `lang != other_lang` such that
        `classification` should be linked to `other_classification`.

        Classifications where links to other language versions makes no sense
        should simply return an empty list.

        Provided is a set of classifications per language (`classifications_per_language`).
        """
        return []


CATEGORIES = {
    "Command": Command,
    "Task": Task,
    "LateTask": LateTask,
    "TemplateSystem": TemplateSystem,
    "PageCompiler": PageCompiler,
    "TaskMultiplier": TaskMultiplier,
    "CompilerExtension": CompilerExtension,
    "MarkdownExtension": MarkdownExtension,
    "RestExtension": RestExtension,
    "MetadataExtractor": MetadataExtractor,
    "ShortcodePlugin": ShortcodePlugin,
    "SignalHandler": SignalHandler,
    "ConfigPlugin": ConfigPlugin,
    "CommentSystem": CommentSystem,
    "PostScanner": PostScanner,
    "Taxonomy": Taxonomy,
}
