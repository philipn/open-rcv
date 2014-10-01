
import glob
import logging
import os
from pathlib import Path
from subprocess import check_output
import webbrowser

from setuptools import Command

DOCS_PATH = "docs"
DOCS_BUILD_PATH = os.path.join(DOCS_PATH, "build")
ENCODING = 'utf-8'
LONG_DESCRIPTION_PATH = "setup_long_description.rst"
README_PATH = "README.md"
# We do not need to actually import the pandoc filters.
PANDOC_HTML_FILTER = "pandocfilters/htmlfilter.py"
PANDOC_RST_FILTER = "pandocfilters/htmlfilter.py"

log = logging.getLogger(os.path.basename(__name__))


def ensure_dir(path):
    if not os.path.exists(path):
        log.info("creating dir: %s" % path)
        os.makedirs(path)


def read(path, encoding=None):
    if encoding is None:
        encoding = ENCODING
    # This implementation was chosen to be compatible across Python 2/3.
    with open(path, 'r', encoding=ENCODING) as f:
        text = f.read()
    return text


def write(text, path, description=None):
    """Write a string to a file."""
    desc = ('%s ' % description) if description else ''
    log.info("writing %sto: %s" % (desc, path))
    with open(path, 'w', encoding=ENCODING) as f:
        f.write(text)


def run_pandoc(args):
    args = ['pandoc'] + args
    log.info("running pandoc in a subprocess: %r" % " ".join(args))
    try:
        stdout = check_output(args)
    except FileNotFoundError as err:
        msg = ("pandoc not found:\n"
               "  -->%s\n"
               "  Did you install pandoc? See the documentation for more info." % err)
        raise Exception(msg)
    return stdout


def update_long_description_file():
    rst = run_pandoc(["--write=rst", "README.md"])
    rst = rst.decode('utf-8')
    write(rst, "setup_long_description.rst", "long_description")


def html_target_path(rel_path):
    return os.path.join(DOCS_BUILD_PATH, rel_path)


def md2html(md_path):
    # --filter ./urltransform.py --write=html --output=README.html README.md
    opath = Path(md_path)
    target_path = html_target_path(str(opath.with_suffix(".html")))
    filter_path = os.path.relpath(PANDOC_HTML_FILTER)
    run_pandoc(["--filter", filter_path, "--write=html",
                "--output", target_path, md_path])
    return target_path


def build_html():
    ensure_dir(DOCS_BUILD_PATH)
    target_readme_path = md2html(README_PATH)

    ensure_dir(html_target_path(DOCS_PATH))
    md_paths = glob.glob(os.path.join(DOCS_PATH, "*.md"))
    for md_path in md_paths:
        md2html(md_path)

    readme_opath = Path(target_readme_path)
    uri = readme_opath.resolve().as_uri()
    log.info("opening web browser to: %s\n-->%s" % (target_readme_path, uri))
    webbrowser.open(uri)


class CommandBase(Command):

    description = None

    # The following three must all be present to avoid errors.
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self._run()
        except FileNotFoundError as err:
            # Raise a new exception because distutils/setuptools does
            # not display the stack trace for these types of errors.
            raise Exception("error occurred during setuptools command")


class BuildHtmlCommand(CommandBase):

    description = "Build HTML from markdown files."

    def _run(self):
        build_html()


class LongDescriptionCommand(CommandBase):

    description = "Update the reST long_description file."

    def _run(self):
        update_long_description_file()
