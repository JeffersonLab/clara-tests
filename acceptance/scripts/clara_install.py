import argparse
import os
import re
import shutil
import subprocess
import sys
import time

from clara_common import get_config_section
from colorama import init as color_init
from colorama import Fore

color_init(autoreset=True)


def print_c(color, msg):
    print color + msg + Fore.RESET


class Project(object):
    def __init__(self, src_dir, data):
        self.name = data['name']
        self.path = os.path.expanduser(os.path.join(src_dir, self.name))
        self.url = data['url']
        self.build_cmds = data['build']
        self.clean_cmds = data['clean']

    def is_present(self):
        return os.path.isdir(self.path)

    def download(self):
        if 'clas12svn' in self.url:
            cmd = 'svn co %s %s' % (self.url, self.path)
        elif 'github' in self.url:
            cmd = 'git clone %s %s' % (self.url, self.path)
        else:
            raise RuntimeError('Bad URL: %s' % self.url)
        print_c(Fore.BLUE, cmd)
        time.sleep(1)
        rc = subprocess.check_call(cmd.split())
        return rc == 0

    def build(self):
        for cmd in self.build_cmds:
            print_c(Fore.BLUE, cmd)
            if re.match(r'^cmake', cmd):
                cmd += ' -DCMAKE_COLOR_MAKEFILE=OFF'
            time.sleep(1)
            rc = subprocess.check_call(cmd, shell=True, cwd=self.path)
            if rc != 0:
                return False
        return True

    def clean(self):
        for cmd in self.clean_cmds:
            print_c(Fore.BLUE, cmd)
            time.sleep(1)
            rc = subprocess.check_call(cmd, shell=True, cwd=self.path)
            if rc != 0:
                return False
        return True


class ProjectManager:
    def __init__(self, src_dir):
        self.src_dir = src_dir
        self.projects = []

    def register_projects(self, data):
        print_c(Fore.YELLOW, "Registering projects...")
        self.projects = [Project(self.src_dir, pd) for pd in data]

    def download_projects(self):
        for p in self.projects:
            print_c(Fore.YELLOW, "Downloading '%s'..." % p.name)
            if not p.is_present():
                stat = p.download()
                if not stat:
                    raise RuntimeError('Could no download %s' % p.name)
                print_c(Fore.GREEN, "'%s' successfully downloaded" % p.name)
            else:
                print "'%s' is already on disk" % p.name

    def build_projects(self, clean):
        for p in self.projects:
            print_c(Fore.YELLOW, "Installing '%s'..." % p.name)
            if p.is_present():
                time.sleep(1)
                if clean:
                    stat = p.clean()
                    if not stat:
                        raise RuntimeError('Could no clean %s' % p.name)
                stat = p.build()
                if not stat:
                    raise RuntimeError('Could no build %s' % p.name)
                print_c(Fore.GREEN, "'%s' successfully installed" % p.name)
            else:
                raise RuntimeError("'%s' is not on disk" % p.name)

    def clean_install_directory(self):
        print_c(Fore.YELLOW, "Removing contents of $CLARA_SERVICES...")
        clara_services = os.getenv('CLARA_SERVICES')
        for f in os.listdir(clara_services):
            path = os.path.join(clara_services, f)
            if os.path.isfile(path):
                os.remove(path)
            else:
                shutil.rmtree(path)


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src-dir", required=True)
    parser.add_argument("--conf-file", required=True)
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--clean-build", action="store_true")
    parser.add_argument("--clean-install", action="store_true")

    return parser.parse_args()


if __name__ == '__main__':
    try:
        args = get_arguments()
        data = get_config_section(args.conf_file, 'projects')

        pm = ProjectManager(args.src_dir)
        pm.register_projects(data)

        if not args.skip_download:
            pm.download_projects()

        if args.clean_install:
            pm.clean_install_directory()

        if not args.skip_build:
            pm.build_projects(args.clean_build)

        print_c(Fore.GREEN, "Done!")
    except Exception as e:
        print_c(Fore.RED, str(e))
        sys.exit(1)
