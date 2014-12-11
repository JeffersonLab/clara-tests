import atexit
import os
import psutil
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


def stop_process(conf):
    def finished_process(proc, limit=25):
        counter = 0
        while proc.is_running():
            counter += 1
            if counter > limit:
                return False
            time.sleep(0.2)
        return True

    def kill_process(proc):
        proc.terminate()
        if not finished_process(proc):
            proc.kill()
            proc.wait()
            return True
        return False

    killed = False
    process = psutil.Process(conf.proc.pid)
    children = process.get_children(recursive=True)
    for proc in children:
        killed = kill_process(proc) or killed
    if not children:
        killed = kill_process(process) or killed

    conf.close_logs()

    if killed:
        raise OSError("Process has been killed")


def stop_all(manager):
    for run in manager.instances.values():
        try:
            stop_process(run)
        except Exception:
            pass
    manager.instances.clear()


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

        clara_conf = ClaraProcessConfig(self.clara,
                                        clara_lang,
                                        clara_instance)
        clara_conf.open_logs()

        clara_proc = subprocess.Popen(clara_conf.cmd,
                                      cwd=clara_conf.cwd,
                                      stdout=clara_conf.out,
                                      stderr=clara_conf.err,
                                      preexec_fn=os.setsid,
                                      env=clara_conf.env)

        for i in range(5):
            if clara_proc.poll() is not None:
                clara_conf.close_logs()
                raise ClaraManagerError('Could not start %s' % key)
            time.sleep(0.4)

        clara_conf.set_proc(clara_proc)

        self.instances[key] = clara_conf

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


if __name__ == "__main__":
    manager = ClaraManager(clara)

    atexit.register(stop_all, manager)
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda num, frame: sys.exit(1))

    manager.run()
