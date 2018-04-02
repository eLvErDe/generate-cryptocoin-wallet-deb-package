import logging
import subprocess
import pathlib
import shutil


class DebActions:
    """ A class running dpkg-buildpackage to generate a package """

    def __init__(self, *, name, tmp_path, extract_path, out_dir):
        """ Well, that's __init__ """

        self.logger = logging.getLogger(self.__class__.__name__)
        self.name = name.lower()
        self.tmp_path = tmp_path
        self.extract_path = extract_path
        self.out_dir = out_dir

    def process(self):
        """ Sequencially run through all steps """

        self.buildpackage()
        self.move_files_to_tmp()

    def log_output(self, output, prefix='', level=logging.INFO):
        """ Turn subprocess call output into logger entries """

        if isinstance(output, bytes):
            output = str(output, 'utf-8')

        for line in output.splitlines():
            self.logger.log(level, prefix + line)

    def buildpackage(self):
        """ Run dpkg-buildpackage to generate the source package """

        cmd = []
        cmd.append('dpkg-buildpackage')
        cmd.append('--build=source')
        cmd.append('--no-sign')
        cmd.append('--no-check-builddeps')
        self.logger.info('About to run: %s', ' '.join(cmd))
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, cwd=self.extract_path, timeout=60)
            self.log_output(output, 'dpkg-buildpackage: ')
        except subprocess.CalledProcessError as e:
            self.log_output(e.output, 'dpkg-buildpackage: ')
            raise

    def move_files_to_tmp(self):
        """ Find source package files and move them outside temporary dir """
        
        files_to_keep = []
        files_to_keep += list(pathlib.Path(self.tmp_path).glob('*.orig.tar.*'))
        files_to_keep += list(pathlib.Path(self.tmp_path).glob('*.debian.tar.*'))
        files_to_keep += list(pathlib.Path(self.tmp_path).glob('*.dsc'))

        generated_files = []
        for file_to_keep in files_to_keep:
            self.logger.info('Moving package file %s to %s', str(file_to_keep), self.out_dir)
            shutil.move(str(file_to_keep), self.out_dir)
            generated_files.append(str(pathlib.Path(self.out_dir, file_to_keep.name)))

        self.logger.info('The following files have been generated: %s', ' '.join(generated_files))
