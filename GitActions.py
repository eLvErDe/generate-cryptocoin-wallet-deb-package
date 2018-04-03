import os
import datetime
import time
import re
import logging
import shlex
import subprocess
import tarfile


class GitActions:
    """ A class implementing all steps to produce a tar archive from a git url and branch/tag """

    def __init__(self, *, name, git_url, git_checkout, tmp_path, version=None):
        """ Well, that's __init__ """

        self.logger = logging.getLogger(self.__class__.__name__)
        self.name = name.lower()
        self.git_url = git_url
        self.git_checkout = git_checkout
        self.tmp_path = tmp_path
        self.clone_path = os.path.join(self.tmp_path, 'git_clone')
        self.version = version
        self.git_short_commit_id =None
        self.archive_path = None
        self.ignore_list = [ '.git', '.gitignore', 'binaries' ]
        if name == 'tune': self.ignore_list.append('depends')

    def process(self):
        """ Sequencially run through all steps """

        self.clone()
        self.checkout()
        self.short_commit_id()
        self.compute_version_after_checkout()
        self.create_archive()

    def log_output(self, output, prefix='', level=logging.INFO):
        """ Turn subprocess call output into logger entries """

        if isinstance(output, bytes):
            output = str(output, 'utf-8')

        for line in output.splitlines():
            self.logger.log(level, prefix + line)

    def clone(self):
        """ Git clone repository """

        cmd = []
        cmd.append('git')
        cmd.append('clone')
        cmd.append('--recursive')
        cmd.append(shlex.quote(self.git_url))
        cmd.append(self.clone_path)
        self.logger.info('About to run: %s', ' '.join(cmd))
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=120)
            self.log_output(output, 'git_clone: ')
            return output
        except subprocess.CalledProcessError as e:
            self.log_output(e.output, 'git_clone: ')
            raise

    def checkout(self):
        """ Git checkout repository at requested branch or tag or commit id """

        cmd = []
        cmd.append('git')
        cmd.append('checkout')
        cmd.append(self.git_checkout)
        self.logger.info('About to run: %s', ' '.join(cmd))
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, cwd=self.clone_path, timeout=10)
            self.log_output(output, 'git_checkout: ')
            return output.strip()
        except subprocess.CalledProcessError as e:
            self.log_output(e.output, 'git_checkout: ')
            raise

    def short_commit_id(self):
        """ Compute short Git commit id to be added to version """

        cmd = []
        cmd.append('git')
        cmd.append('log')
        cmd.append('-1')
        cmd.append('--pretty=format:%h')
        self.logger.info('About to run: %s', ' '.join(cmd))
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, cwd=self.clone_path, timeout=10)
        self.git_short_commit_id = str(output, 'utf-8').strip()

    def latest_tag_from_checkout(self):
        """ Find latest tag from the branch we checked in """

        cmd = []
        cmd.append('git')
        cmd.append('describe')
        cmd.append('--abbrev=0')
        cmd.append('--tags')
        cmd.append(self.git_checkout)
        self.logger.info('About to run: %s', ' '.join(cmd))
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, cwd=self.clone_path, timeout=10)
            output = str(output, 'utf-8').strip()
            self.logger.info('Newest Git tag found at this checkout: %s', output)
            return output
        except subprocess.CalledProcessError as e:
            self.log_output(e.output, 'git_desc: ')
            return None

    def git_tag_commit_id(self, git_tag_branch, length=None):
        """ Return Git commit checkout tag or branch name """

        cmd = []
        cmd.append('git')
        cmd.append('rev-parse')
        cmd.append('--verify')
        cmd.append(git_tag_branch+'^{commit}')
        if length is not None:
            cmd.append('--short='+str(length))
        self.logger.info('About to run: %s', ' '.join(cmd))
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, cwd=self.clone_path, timeout=10)
            output = str(output, 'utf-8').strip()
            self.logger.info('Git short commit id for Git tag %s found: %s', git_tag_branch, output)
            return output
        except subprocess.CalledProcessError as e:
            self.log_output(e.output, 'git_rev_parse: ')
            return None

    def create_archive(self):
        """ Create the tar archive, stripping git stuff and adding relative folder with project name and version """

        # Forget git archive here because it does not handle submodules

        filename = '%s_%s.orig.tar.gz' % (self.name, self.version)
        self.archive_path = os.path.join(self.tmp_path, filename)
        self.logger.info('Generating upstream tarball archive at %s', self.archive_path)
        self.logger.info('Ignoring the following files/directories: %s', self.ignore_list)

        def relative_arcname_and_filter(tarinfo):

            # Compute tarinfo.name to be relative from clone_path
            # 1. Add leading /
            tarinfo.name = os.path.join(os.sep, tarinfo.name)
            # 2. Make it relative to clone path 
            tarinfo.name = os.path.relpath(tarinfo.name, self.clone_path)

            # 3. Filter GIT related files
            # head will be empty string if there is no folder in path
            head, tail = os.path.split(tarinfo.name)
            to_filter = head if head != '' else tail
            if to_filter in self.ignore_list:
                return None

            # 4. Add a top folder containing project-version
            tarinfo.name = os.path.join(self.name + '-' + self.version, tarinfo.name)

            return tarinfo

        with tarfile.open(self.archive_path, mode='w:gz') as archive:
            archive.add(self.clone_path, recursive=True, filter=relative_arcname_and_filter)

    def compute_version_after_checkout(self):
        """ After checkout use latest tag from branch to generate a base version or 0.0, then add timestamp, checkout and short Git commit id """

        if self.version is not None:
            return

        latest_tag_from_checkout = self.latest_tag_from_checkout()
        if latest_tag_from_checkout is not None:
            re_match = re.search(r'^[vV]?([0-9\.]+)(([ -_])?(dev|rc[0-9]*|beta[0-9]*|alpha[0-9]*))?$', latest_tag_from_checkout)
            if re_match:
                self.version = re_match.group(1)
                if re_match.group(4) is not None:
                    self.version += '~'
                    self.version += re_match.group(4)
            else:
                self.version = '0.0'
        else:
            self.version = '0.0'


        if latest_tag_from_checkout is not None:
            latest_tag_from_checkout_commit_id = self.git_tag_commit_id(latest_tag_from_checkout, length=len(self.git_short_commit_id))
        else:
            latest_tag_from_checkout_commit_id = None

        if self.git_short_commit_id == latest_tag_from_checkout_commit_id:
            self.logger.info('Git commit id of request checkout matches newest tag, looks like it is a stable release')
        else:
            self.version = '{version}+git{timestamp}.{branch}.{commit}'.format(
                version=self.version,
                timestamp=datetime.datetime.now(tz=datetime.timezone.utc).strftime('%Y%m%d'),
                branch=self.git_checkout,
                commit=self.git_short_commit_id,
            )
        self.logger.info('Upstream version set to %s according to GIT checkout, hit CTRL+C now and pass --version my.version if it is not correct', self.version)
        time.sleep(5)
