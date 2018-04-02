import os
import logging
import subprocess
import datetime
import pathlib
import jinja2


FILE_FOLDER = os.path.dirname(os.path.abspath(__file__))


class TplActions:
    """ A class generating debian packaging file from templates """

    @staticmethod
    def get_locale_tz():
        return datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo

    @staticmethod
    def now_debian_changelog(tzinfo):
        return datetime.datetime.strftime(datetime.datetime.now(tzinfo), '%a, %d %b %Y %H:%M:%S %z')

    def __init__(self, *, name, tmp_path, archive_path, git_url, version, debian_revision, maintainer_name, maintainer_email):
        """ Well, that's __init__ """

        self.logger = logging.getLogger(self.__class__.__name__)
        self.name = name.lower()
        self.tmp_path = tmp_path
        self.archive_path = archive_path
        self.git_url = git_url
        self.version = version
        self.debian_revision = debian_revision
        self.maintainer_name = maintainer_name
        self.maintainer_email = maintainer_email
        self.extract_path = os.path.join(self.tmp_path, '%s-%s' % (self.name, self.version))


    def process(self):
        """ Sequencially run through all steps """

        self.untar()
        self.jinja2_render()

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

    def jinja2_render(self):
        """ Loop around files in templates folder and render them """

        template_folder = pathlib.Path(FILE_FOLDER, 'templates')
        data = {
            'name': self.name,
            'git_url': self.git_url,
            'version': self.version,
            'debian_revision': self.debian_revision,
            'timestamp': self.now_debian_changelog(self.get_locale_tz()),
            'maintainer_name': self.maintainer_name,
            'maintainer_email': self.maintainer_email,
        }
        self.logger.info('Maintainer set to %s <%s>', self.maintainer_name, self.maintainer_email)

        # First iteration to create folder
        for abs_template_file in template_folder.glob('**/*'):

            relative_template_file = abs_template_file.relative_to(template_folder)
            dest_template_file =  pathlib.Path(self.extract_path, 'debian', relative_template_file)

            # Render destination filename using Jinja
            dest_template_file = jinja2.Environment(loader=jinja2.BaseLoader()).from_string(str(dest_template_file)).render(**data)

            if abs_template_file.is_dir():
                self.logger.info('Creating directory: %s', dest_template_file)
                os.makedirs(dest_template_file)

        # Secoond iteration to create files
        for abs_template_file in template_folder.glob('**/*'):

            relative_template_file = abs_template_file.relative_to(template_folder)
            dest_template_file =  pathlib.Path(self.extract_path, 'debian', relative_template_file)

            # Render destination filename using Jinja
            dest_template_file = jinja2.Environment(loader=jinja2.BaseLoader()).from_string(str(dest_template_file)).render(**data)

            if abs_template_file.is_file():
                self.logger.info('Rendering file from template: %s', dest_template_file)
                with open(abs_template_file, 'r') as template_fp:
                    jinja2.Template(template_fp.read()).stream(**data).dump(dest_template_file)

        import time
        time.sleep(60)
