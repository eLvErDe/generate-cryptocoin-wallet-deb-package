import os
import logging
import subprocess


class TemplateActions:
    """ A class implementing all steps to produce a tar archive from a git url and branch/tag """

    def __init__(self, *, name, tmp_path, archive_path, git_url, version):
        """ Well, that's __init__ """

        self.logger = logging.getLogger(self.__class__.__name__)
        self.name = name.lower()
        self.tmp_path = tmp_path
        self.archive_path = archive_path
        self.git_url = git_url
        self.version = version
        self.extract_path = os.path.join(self.tmp_path, '%s-%s' % (self.name, self.version))

    def process(self):
        """ Sequencially run through all steps """

        self.untar()

    def log_output(self, output, prefix='', level=logging.INFO):
        """ Turn subprocess call output into logger entries """

        if isinstance(output, bytes):
            output = str(output, 'utf-8')

        for line in output.splitlines():
            self.logger.log(level, prefix + line)

    def untar(self):
        """ Untar previously generated archive, go for tar because tarfile module is awful to use """

        cmd = []
        cmd.append('tar')
        cmd.append('xf')
        cmd.append(self.archive_path)
        cmd.append('-C')
        cmd.append(self.tmp_path)
        self.logger.info('About to run: %s', ' '.join(cmd))
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=60)
            self.log_output(output, 'untar: ')
        except subprocess.CalledProcessError as e:
            self.log_output(e.output, 'untar: ')
            raise

        self.logger.info('Upstream source tarball extracted to %s', self.extract_path)
