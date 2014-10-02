import unittest
import mock
import os
import zmq

from clara_manager import ClaraManager
from clara_manager import ClaraManagerError
from clara_manager import host_ip
from clara_manager import __name__ as cm

clara = {
    'logs': '/clara/logs',
    'python': {
        'fullpath': '/clara/python',
        'platform': 'python -u core/system/Platform.py',
        'dpe': 'python -u core/system/Dpe.py',
    },
}


class testClaraManager(unittest.TestCase):

    def test_start_clara_wrong_instance(self):
        manager = ClaraManager(clara)
        with self.assertRaises(ClaraManagerError):
            manager.start_clara('java', 'monitor')

    def test_start_clara_wrong_type(self):
        manager = ClaraManager(clara)
        with self.assertRaises(ClaraManagerError):
            manager.start_clara('erlang', 'dpe')

    def test_start_clara_python_platform(self):
        wd = '/clara/python'
        cmd = ['python', '-u', 'core/system/Platform.py']

        with mock.patch.dict(os.environ, clear=True):
            env = {'PYTHONPATH': '/clara/python'}
            self._assert_start_clara('python', 'platform', cmd, wd, env)

        with mock.patch.dict(os.environ, {'PYTHONPATH': '/opt/python'}):
            env = dict(os.environ, PYTHONPATH='/clara/python:/opt/python')
            self._assert_start_clara('python', 'platform', cmd, wd, env)

    def _assert_start_clara(self, lang, instance, command, working_dir,
                            env=os.environ):
        def log_files(*args):
            return args[0]

        out_log = "/clara/logs/%s-%s-%s.log" % (host_ip, lang, instance)
        err_log = "/clara/logs/%s-%s-%s.err" % (host_ip, lang, instance)

        manager = ClaraManager(clara)

        with mock.patch('%s.open' % cm, mock.mock_open(), create=True) as o, \
                mock.patch('%s.subprocess' % cm) as sp:

            o.side_effect = log_files
            sp.Popen.return_value = 'ok'

            manager.start_clara(lang, instance)

            log_calls = [mock.call(out_log, 'w+'), mock.call(err_log, 'w+')]
            o.assert_has_calls(log_calls)

            sp.Popen.assert_called_with(command,
                                        env=env,
                                        cwd=working_dir,
                                        stdout=out_log,
                                        stderr=err_log)

            key = lang + "/" + instance
            self.assertIn(key, manager.instances)

            clara_run = manager.instances[key]

            self.assertEquals(clara_run.proc, 'ok')
            self.assertSequenceEqual(clara_run.logs, [out_log, err_log])

    @mock.patch('zmq.Socket')
    @mock.patch('zmq.Context')
    def test_zmq_server_is_up(self, mock_ctx, mock_sck):
        manager = ClaraManager(clara)

        ctx = mock_ctx.return_value
        sck = mock_sck.return_value

        ctx.socket.return_value = sck
        sck.recv.side_effect = NotImplementedError

        with self.assertRaises(NotImplementedError):
            manager.run()

        ctx.socket.assert_called_once_with(zmq.REP)
        sck.bind.assert_called_once_with("tcp://*:7788")


if __name__ == '__main__':
    unittest.main()
