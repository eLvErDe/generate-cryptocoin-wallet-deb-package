#!/usr/bin/python3

import sys
import argparse
import logging
import tempfile

from GitActions import GitActions

if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO, format='%(levelname)-8s [%(name)-12s] %(message)s', stream=sys.stdout)
    logger = logging.getLogger('main')

    def cli_arguments():
        parser = argparse.ArgumentParser(description='Create a source Debian package for any cryptocoin wallet')
        parser.add_argument('-n', '--name',         required=True,    type=str, help='Coin name',                     metavar='raven')
        parser.add_argument('-g', '--git-url',      required=True,    type=str, help='GIT project url',               metavar='https://github.com/RavenProject/Ravencoin.git')
        parser.add_argument('-c', '--git-checkout', default='master', type=str, help='GIT tag or branch to checkout', metavar='master or v0.15.99.0')
        parser.add_argument('-v', '--version',      required=False,   type=str, help='Force package version',         metavar='1.0')
        return parser.parse_args()

    config = cli_arguments()

    with tempfile.TemporaryDirectory() as tmp_path:

        git_actions = GitActions(
            name=config.name,
            git_url=config.git_url,
            git_checkout=config.git_checkout,
            version=config.version,
            tmp_path=tmp_path,
        )

        git_actions.process()
