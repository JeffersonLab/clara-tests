import atexit
import os
import socket
import subprocess
import sys
import time

clara = {
    'services': '/home/vagrant/clara/services',
    'logs': '/home/vagrant/clara/log',
    'python': {
        'fullpath': '/home/vagrant/clara/src/python',
        'platform': 'python -u core/system/Platform.py',
        'dpe': 'python -u core/system/Dpe.py',
    },
}

host_ip = socket.gethostbyname(socket.gethostname())


def stop_all(manager):
    for run in manager.instances.values():
        run.proc.terminate()
        for log in run.logs:
            log.close()


class ClaraProcess():
    def __init__(self, proc, logs):
        self.proc = proc
        self.logs = logs


class ClaraManager():
    def __init__(self, clara):
        self.clara = clara
        self.instances = {}
        self.orchestrators = []
        self.logs = []

    def start_clara(self, clara_lang, clara_instance):

        if clara_lang not in self.clara:
            return False

        if clara_instance != 'platform' and clara_instance != 'dpe':
            return False

        key = '%s/%s' % (clara_lang, clara_instance)
        if key in self.instances:
            return False

        clara_conf = self.clara[clara_lang]

        clara_env = self._get_clara_env(clara_lang)
        clara_dir = clara_conf['fullpath']
        clara_command = clara_conf[clara_instance].split()
        clara_out = self._get_clara_logfile(clara_lang, clara_instance, "log")
        clara_err = self._get_clara_logfile(clara_lang, clara_instance, "err")

        clara_proc = subprocess.Popen(clara_command,
                                      cwd=clara_dir,
                                      stdout=clara_out,
                                      stderr=clara_err,
                                      env=clara_env)

        self.instances[key] = ClaraProcess(clara_proc, [clara_out, clara_err])

    def _get_clara_logfile(self, clara_type, clara_instance, log_ext):
        name = '%s-%s-%s.%s' % (host_ip, clara_type, clara_instance, log_ext)
        return open(os.path.join(self.clara['logs'], name), "w+")

    def _get_clara_env(self, clara_lang):
        env = os.environ.copy()
        if clara_lang == 'python':
            clara_path = self.clara[clara_lang]['fullpath']
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = clara_path + ":" + env['PYTHONPATH']
            else:
                env['PYTHONPATH'] = clara_path
        return env


if __name__ == "__main__":
    manager = ClaraManager(clara)
    atexit.register(stop_all, manager)

    manager.start_clara(sys.argv[1], sys.argv[2])

    while True:
        time.sleep(1)
