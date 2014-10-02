import atexit
import os
import socket
import subprocess
import time
import zmq

from daemon import runner

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
port = "7788"


def stop_process(run):
    run.proc.terminate()
    for log in run.logs:
        log.close()


def stop_all(manager):
    for run in manager.instances.values():
        stop_process(run)
    manager.instances.clear()


class ClaraProcess():
    def __init__(self, proc, logs):
        self.proc = proc
        self.logs = logs


class ClaraManagerError(Exception):
    pass


class ClaraManager():
    def __init__(self, clara):
        self.clara = clara
        self.instances = {}
        self.orchestrators = []
        self.logs = []

        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path = '/home/vagrant/clara/manager.pid'
        self.pidfile_timeout = 5

    def run(self):
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind("tcp://*:%s" % port)
        time.sleep(0.1)
        while True:
            msg = socket.recv()
            res = self.dispatch_request(msg)
            socket.send_multipart(res)

    def dispatch_request(self, msg):
        try:
            if not msg:
                return ['ERROR', 'Empty request']
            req = msg.split('/')
            if len(req) != 4:
                return ['ERROR', 'Bad request: %s' % msg]
            _, lang, instance, action = req
            if action == 'start':
                self.start_clara(lang, instance)
            elif action == 'stop':
                self.stop_clara(lang, instance)
            else:
                return ['ERROR', 'Unsupported action: %s' % action]
            return ['SUCCESS', '']
        except ClaraManagerError as e:
            return ['ERROR', str(e)]
        except Exception as e:
            return ['ERROR', "Unexpected exception: " + str(e)]

    def start_clara(self, clara_lang, clara_instance):
        if clara_lang not in self.clara:
            raise ClaraManagerError('Bad language: %s' % clara_lang)

        if clara_instance != 'platform' and clara_instance != 'dpe':
            raise ClaraManagerError('Bad instance: %s' % clara_instance)

        key = '%s/%s' % (clara_lang, clara_instance)
        if key in self.instances:
            raise ClaraManagerError('%s already running!' % key)

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

    def stop_clara(self, clara_lang, clara_instance):
        if clara_lang not in self.clara:
            raise ClaraManagerError('Bad language: %s' % clara_lang)

        if clara_instance != 'platform' and clara_instance != 'dpe':
            raise ClaraManagerError('Bad instance: %s' % clara_instance)

        key = '%s/%s' % (clara_lang, clara_instance)
        if key not in self.instances:
            raise ClaraManagerError('%s is not running!' % key)

        run = self.instances.pop(key)
        stop_process(run)

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

    daemon_runner = runner.DaemonRunner(manager)
    daemon_runner.daemon_context.working_directory = '/home/vagrant/clara'
    daemon_runner.daemon_context.uid = 1000
    daemon_runner.daemon_context.gid = 1000
    daemon_runner.do_action()
