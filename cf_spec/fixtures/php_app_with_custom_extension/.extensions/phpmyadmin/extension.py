"""PHPMyAdmin Extension

Downloads, installs and configures PHPMyAdmin
"""
import os
import os.path
import logging
from build_pack_utils import utils


_log = logging.getLogger('phpmyadmin')


DEFAULTS = utils.FormattedDict({
    'PHPMYADMIN_VERSION': '4.3.12',
    'PHPMYADMIN_PACKAGE': 'phpMyAdmin-{PHPMYADMIN_VERSION}-english.tar.gz',
    'PHPMYADMIN_HASH': '707064d1efc37acc8e6fd7ddcc9030616ae32562',
    'PHPMYADMIN_URL': 'http://sourceforge.net/projects/phpmyadmin/'
                      'files/phpMyAdmin/{PHPMYADMIN_VERSION}/'
                      '{PHPMYADMIN_PACKAGE}/download#'
})


# Extension Methods
def preprocess_commands(ctx):
    return ()


def service_commands(ctx):
    return {}


def service_environment(ctx):
    return {}


def compile(install):
    print 'Installing PHPMyAdmin %s' % DEFAULTS['PHPMYADMIN_VERSION']
    ctx = install.builder._ctx
    inst = install._installer
    workDir = os.path.join(ctx['TMPDIR'], 'phpmyadmin')
    inst.install_binary_direct(
        DEFAULTS['PHPMYADMIN_URL'],
        DEFAULTS['PHPMYADMIN_HASH'],
        workDir,
        fileName=DEFAULTS['PHPMYADMIN_PACKAGE'],
        strip=True)
    (install.builder
        .move()
        .everything()
        .under('{BUILD_DIR}/htdocs')
        .into(workDir)
        .done())
    (install.builder
        .move()
        .everything()
        .under(workDir)
        .where_name_does_not_match('^%s/setup/.*$' % workDir)
        .into('{BUILD_DIR}/htdocs')
        .done())
    return 0
