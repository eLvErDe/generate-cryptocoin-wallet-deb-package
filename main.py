#!/usr/bin/python3

import sys
import argparse
import logging
import tempfile
import os

from GitActions import GitActions
from TemplateActions import TemplateActions


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO, format='%(levelname)-8s [%(name)-12s] %(message)s', stream=sys.stdout)
    logger = logging.getLogger('main')

    # Attempt to find default user fullname
    default_username = os.getenv('DEBFULLNAME', None)
    if default_username is None: default_username = os.getenv('LOGNAME', None)
    if default_username is None: default_username = 'someone'

    # Attempt to find user email address
    default_email = os.getenv('DEBEMAIL', None)
    if default_email is None: default_email = os.getenv('EMAIL', None)
    if default_email is None: default_email = '%s@localhost' % default_username

    def cli_arguments():
        """ Command line arguments """

        parser = argparse.ArgumentParser(description='Create a source Debian package for any cryptocoin wallet', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('-n', '--name',         required=True,    type=str, help='Coin name',                     metavar='raven')
        parser.add_argument('-g', '--git-url',      required=True,    type=str, help='GIT project url',               metavar='https://github.com/RavenProject/Ravencoin.git')
        parser.add_argument('-c', '--git-checkout', default='master', type=str, help='GIT tag or branch to checkout', metavar='master or v0.15.99.0')
        parser.add_argument('-v', '--version',      required=False,   type=str, help='Force package version',         metavar='1.0')
        parser.add_argument('-r', '--revision',     default=1,        type=int, help='Debian package revision',       metavar='1')
        parser.add_argument('-m', '--maintainer-name',  default=default_username, type=str, help='Debian package maintainer pretty name',   metavar='John Doe')
        parser.add_argument('-e', '--maintainer-email', default=default_email,    type=str, help='Debian package maintainer email address', metavar='john@doe.com')
        return parser.parse_args()

    config = cli_arguments()

    with tempfile.TemporaryDirectory() as tmp_path:

        # Create upstream tar archive

        git_actions = GitActions(
            name=config.name,
            git_url=config.git_url,
            git_checkout=config.git_checkout,
            version=config.version,
            tmp_path=tmp_path,
        )
        git_actions.process()

        # Generate Debian packaging from templatized Bitcoin one

        template_actions = TemplateActions(
            name=config.name,
            tmp_path=tmp_path,
            archive_path=git_actions.archive_path,
            git_url=config.git_url,
            version=git_actions.version,
            debian_revision=config.revision,
            maintainer_name=config.maintainer_name,
            maintainer_email=config.maintainer_email,
        )
        template_actions.process()
