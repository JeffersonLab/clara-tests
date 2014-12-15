import atexit
import os
import signal
import socket
import subprocess
import sys
import time
import zmq

clara = {
    'services': '/home/vagrant/clara/services',
    'logs': '/home/vagrant/clara/services/log',
    'python': {
        'fullpath': '/home/vagrant/clara/dev/python',
        'platform': 'python -u core/system/Platform.py',
        'dpe': 'python -u core/system/Dpe.py',
    },
    'java': {
        'fullpath': '/home/vagrant/clara/services',
        'platform': './bin/clara-platform',
        'dpe': './bin/clara-dpe -host 10.11.1.100 -log',
    },
}

host_ip = socket.gethostbyname(socket.gethostname())
port = "7788"


def finished_process(proc, limit=25):
    counter = 0
    while proc.poll() is None:
        counter += 1
        if counter > limit:
            return False
        time.sleep(0.2)
    return True


def stop_process(run):
    killed = False

    run.proc.terminate()
    if not finished_process(run.proc):
        run.proc.kill()
        run.proc.wait()
        killed = True

    for log in run.logs:
        log.close()

    if killed:
        raise OSError("Process has been killed")


def stop_all(manager):
    for run in manager.instances.values():
        try:
            stop_process(run)
        except Exception:
            pass
    manager.instances.clear()


class ClaraProcess():
    def __init__(self, proc, logs):
        self.proc = proc
        self.logs = logs


class ClaraProcessConfig():
    def __init__(self, clara, lang='java', instance='platform'):
        self._conf = clara[lang]
        self._logs = clara['logs']
        self._lang = lang
        self._instance = instance

        self.cmd = self._conf[instance].split()
        self.cwd = self._conf['fullpath']
        self.proc = None
        self.out = None
        self.err = None
        self.env = self._env()

    def open_logs(self):
        self.out = self._open_log('log')
        self.err = self._open_log('err')

    def close_logs(self):
        self.out.close()
        self.err.close()

        self.out = None
        self.err = None

    def set_proc(self, proc):
        self.proc = proc

    def _open_log(self, ext):
        name = '%s-%s-%s.%s' % (host_ip, self._lang, self._instance, ext)
        return open(os.path.join(self._logs, name), "w+")

    def _env(self):
        env = os.environ.copy()
        if self._lang == 'python':
            fullpath = self._conf['fullpath']
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = fullpath + ":" + env['PYTHONPATH']
            else:
                env['PYTHONPATH'] = fullpath
        elif self._lang == 'java':
            fullpath = self._conf['fullpath']
            env['CLARA_SERVICES'] = fullpath
        return env


class ClaraManagerError(Exception):
    pass


class ClaraManager():
    def __init__(self, clara):
        self.clara = clara
        self.instances = {}
        self.orchestrators = []
        self.logs = []

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
            req = msg.split(':')

            if len(req) != 4:
                return ['ERROR', 'Bad request: "%s"' % msg]

            _, action, lang, instance = req
            if action == 'start':
                self.start_clara(lang, instance)
            elif action == 'stop':
                if lang == 'all' or instance == 'all':
                    stop_all(self)
                else:
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
        elif clara_lang == 'java':
            clara_path = self.clara[clara_lang]['fullpath']
            env['CLARA_SERVICES'] = clara_path
        return env


if __name__ == "__main__":
    manager = ClaraManager(clara)

    atexit.register(stop_all, manager)
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda num, frame: sys.exit(1))

    manager.run()
