import getpass
import pexpect
import sys

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


if __name__ == '__main__':
    try:
        accept_jlab_svn_certificate()
        print Fore.GREEN + "Done!"
    except Exception as e:
        print Fore.RED + str(e)
        sys.exit(1)
