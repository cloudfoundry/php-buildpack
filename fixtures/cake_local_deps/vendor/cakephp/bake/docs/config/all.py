# Global configuration information used across all the
# translations of documentation.
#
# Import the base theme configuration
from cakephpsphinx.config.all import *

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#

# The full version, including alpha/beta/rc tags.
release = '1.x'

# The search index version.
search_version = 'bake-1'

# The marketing display name for the book.
version_name = ''

# Project name shown in the black header bar
project = 'CakePHP Bake'

# Other versions that display in the version picker menu.
version_list = [
    {'name': '1.x', 'number': '/bake/1.x', 'title': '1.x', 'current': True},
    # {'name': '2.x', 'number': '/bake/2.x', 'title': '2.x'},
]

# Languages available.
languages = ['en', 'es', 'fr', 'ja', 'pt', 'ru']

# The GitHub branch name for this version of the docs
# for edit links to point at.
branch = 'master'

# Current version being built
version = '1.x'

# Language in use for this directory.
language = 'en'

show_root_link = True

repository = 'cakephp/bake'

source_path = 'docs/'

hide_page_contents = ('search', '404', 'contents')
