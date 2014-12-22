import argparse
import getpass
import os
import pexpect
import re
import shutil
import subprocess
import sys
import time

from clara_common import get_config_section
from colorama import init as color_init
from colorama import Fore

color_init(autoreset=True)


def query_yes_no(question, default="yes"):
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)
    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def send_jlab_credentials(proc):
    user_prompt = "Username: "
    proc.expect_exact(user_prompt)
    user = raw_input("Introduce your JLab username: ")
    proc.sendline(user)

    proc.expect_exact("Password for '%s': " % user)
    password = getpass.getpass("Introduce your JLab password: ")
    proc.sendline(password)

    store_prompt = "Store password unencrypted \(yes/no\)\? "
    i = proc.expect([user_prompt, store_prompt])
    if i == 1:
        store = query_yes_no("Store password unencrypted?")
        if store:
            proc.sendline("yes")
        else:
            proc.sendline("no")
    else:
        raise RuntimeError("Bad JLab credentials")


def accept_jlab_svn_certificate():
    print Fore.YELLOW + "Configuring JLab SVN credentials..."

    jlab_svn = 'https://clas12svn.jlab.org/repos/'
    svn_cmd = 'svn info %s' % jlab_svn
    svn_proc = pexpect.spawn(svn_cmd)

    vm_prompt = "Password for 'vagrant': "
    user_prompt = "Password for '\w+': "
    svn_prompt = ".R.eject, accept .t.emporarily or accept .p.ermanently\? "
    i = svn_proc.expect([svn_prompt, vm_prompt, user_prompt, pexpect.EOF])

    if i == 0:
        svn_proc.sendline('p')
        svn_proc.expect_exact(vm_prompt)
        svn_proc.sendline()
        send_jlab_credentials(svn_proc)
        svn_proc.expect(pexpect.EOF)
    elif i == 1:
        svn_proc.sendline()
        send_jlab_credentials(svn_proc)
        svn_proc.expect(pexpect.EOF)


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
        print Fore.BLUE + cmd
        time.sleep(1)
        rc = subprocess.check_call(cmd.split())
        return rc == 0

    def build(self):
        for cmd in self.build_cmds:
            print Fore.BLUE + cmd
            if re.match(r'^cmake', cmd):
                cmd += ' -DCMAKE_COLOR_MAKEFILE=OFF'
            time.sleep(1)
            rc = subprocess.check_call(cmd, shell=True, cwd=self.path)
            if rc != 0:
                return False
        return True

    def clean(self):
        for cmd in self.clean_cmds:
            print Fore.BLUE + cmd
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
        print Fore.YELLOW + "Registering projects..."
        self.projects = [Project(self.src_dir, pd) for pd in data]

    def download_projects(self):
        for p in self.projects:
            print Fore.YELLOW + "Downloading '%s'..." % p.name
            if not p.is_present():
                stat = p.download()
                if not stat:
                    raise RuntimeError('Could no download %s' % p.name)
                print Fore.GREEN + "'%s' successfully downloaded" % p.name
            else:
                print "'%s' is already on disk" % p.name

    def build_projects(self, clean):
        for p in self.projects:
            print Fore.YELLOW + "Installing '%s'..." % p.name
            if p.is_present():
                time.sleep(1)
                if clean:
                    stat = p.clean()
                    if not stat:
                        raise RuntimeError('Could no clean %s' % p.name)
                stat = p.build()
                if not stat:
                    raise RuntimeError('Could no build %s' % p.name)
                print Fore.GREEN + "'%s' successfully installed" % p.name
            else:
                raise RuntimeError("'%s' is not on disk" % p.name)

    def clean_install_directory(self):
        print Fore.YELLOW + "Removing contents of $CLARA_SERVICES..."
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
            accept_jlab_svn_certificate()
            pm.download_projects()

        if args.clean_install:
            pm.clean_install_directory()

        if not args.skip_build:
            pm.build_projects(args.clean_build)

        print Fore.GREEN + "Done!"
    except Exception as e:
        print Fore.RED + str(e)
        sys.exit(1)
