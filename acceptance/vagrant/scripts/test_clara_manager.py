import unittest
import mock
import os
import zmq

from clara_manager import ClaraManager
from clara_manager import ClaraManagerError
from clara_manager import ClaraProcess
from clara_manager import stop_process
from clara_manager import stop_all
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

    def test_start_clara_bad_instance(self):
        manager = ClaraManager(clara)
        with self.assertRaises(ClaraManagerError) as e:
            manager.start_clara('python', 'monitor')
        msg = 'Bad instance: monitor'
        self.assertEquals(str(e.exception), msg)

    def test_start_clara_bad_lang(self):
        manager = ClaraManager(clara)
        with self.assertRaises(ClaraManagerError) as e:
            manager.start_clara('erlang', 'dpe')
        msg = 'Bad language: erlang'
        self.assertEquals(str(e.exception), msg)

    def test_start_clara_is_running(self):
        manager = ClaraManager(clara)
        manager.instances = {'python/dpe': None}

        with self.assertRaises(ClaraManagerError) as e:
            manager.start_clara('python', 'dpe')
        msg = 'python/dpe already running!'
        self.assertEquals(str(e.exception), msg)

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

    def test_stop_clara_bad_instance(self):
        manager = ClaraManager(clara)

        with self.assertRaises(ClaraManagerError) as e:
            manager.stop_clara('python', 'monitor')
        msg = 'Bad instance: monitor'
        self.assertEquals(str(e.exception), msg)

    def test_stop_clara_bad_lang(self):
        manager = ClaraManager(clara)

        with self.assertRaises(ClaraManagerError) as e:
            manager.stop_clara('erlang', 'python')
        msg = 'Bad language: erlang'
        self.assertEquals(str(e.exception), msg)

    def test_stop_clara_not_running(self):
        manager = ClaraManager(clara)

        with self.assertRaises(ClaraManagerError) as e:
            manager.stop_clara('python', 'dpe')
        msg = 'python/dpe is not running!'
        self.assertEquals(str(e.exception), msg)

    @mock.patch('clara_manager.stop_process')
    def test_stop_clara(self, mock_stop):
        run1 = ClaraProcess("1", None)
        run2 = ClaraProcess("2", None)
        run3 = ClaraProcess("3", None)
        manager = ClaraManager(clara)
        manager.instances = {
            'python/dpe': run1, 'python/platform': run2, 'java/dpe': run3
        }
        result = {'python/platform': run2, 'java/dpe': run3}

        manager.stop_clara('python', 'dpe')

        mock_stop.assert_called_once_with(run1)
        self.assertDictEqual(manager.instances, result)

    def test_stop_process(self):
        out_log = mock.Mock()
        err_log = mock.Mock()
        proc = mock.Mock()
        run = ClaraProcess(proc, [out_log, err_log])

        proc.poll.return_value = 0
        stop_process(run)

        proc.terminate.assert_called_once_with()
        self.assertTrue(not proc.kill.called)

        out_log.close.assert_called_once_with()
        err_log.close.assert_called_once_with()

    @mock.patch('time.sleep')
    def test_stop_process_with_kill(self, mock_t):
        proc = mock.Mock()
        run = ClaraProcess(proc, [])

        proc.poll.return_value = None

        with self.assertRaises(OSError):
            stop_process(run)

        proc.kill.assert_called_once_with()
        proc.wait.assert_called_once_with()

    @mock.patch('clara_manager.stop_process')
    def test_stop_all(self, mock_sp):
        manager = ClaraManager(clara)
        manager.instances = {'p/d': 'p1', 'p/p': 'p2', 'j/d': 'p3'}

        stop_all(manager)

        mock_sp.assert_any_call('p1')
        mock_sp.assert_any_call('p2')
        mock_sp.assert_any_call('p3')
        self.assertEqual(mock_sp.call_count, 3)
        self.assertTrue(not manager.instances)

    @mock.patch('zmq.Socket')
    @mock.patch('zmq.Context')
    @mock.patch('time.sleep')
    def test_zmq_server_is_up(self, mock_t, mock_ctx, mock_sck):
        manager = ClaraManager(clara)

        ctx = mock_ctx.return_value
        sck = mock_sck.return_value

        ctx.socket.return_value = sck
        sck.recv.side_effect = NotImplementedError

        with self.assertRaises(NotImplementedError):
            manager.run()

        ctx.socket.assert_called_once_with(zmq.REP)
        sck.bind.assert_called_once_with("tcp://*:7788")

    @mock.patch('clara_manager.ClaraManager.dispatch_request')
    @mock.patch('zmq.Socket')
    @mock.patch('zmq.Context')
    @mock.patch('time.sleep')
    def test_zmq_server_reply(self, mock_t, mock_ctx, mock_sck, mock_dr):
        manager = ClaraManager(clara)
        msg = 'clara:start:python:dpe'
        res = ["SUCCESS", ""]

        sck = mock_sck.return_value
        mock_ctx.return_value.socket.return_value = sck

        sck.recv.return_value = msg
        mock_dr.return_value = res
        sck.send_multipart.side_effect = NotImplementedError

        with self.assertRaises(NotImplementedError):
            manager.run()

        sck.recv.assert_called_once_with()
        mock_dr.assert_called_once_with(msg)
        sck.send_multipart.assert_called_once_with(res)

    def test_dispatch_empty_request(self):
        manager = ClaraManager(clara)
        msg = ''

        res = manager.dispatch_request(msg)

        self.assertSequenceEqual(res, ['ERROR', 'Empty request'])

    def test_dispatch_bad_request(self):
        manager = ClaraManager(clara)
        msg = 'clara:start'

        res = manager.dispatch_request(msg)

        self.assertSequenceEqual(res, ['ERROR', 'Bad request: "clara:start"'])

    def test_dispatch_bad_action(self):
        manager = ClaraManager(clara)
        msg = 'clara:launch:python:dpe'

        res = manager.dispatch_request(msg)

        self.assertSequenceEqual(res, ['ERROR', 'Unsupported action: launch'])

    @mock.patch('clara_manager.ClaraManager.start_clara')
    def test_dispatch_start_request(self, mock_sc):
        manager = ClaraManager(clara)
        msg = 'clara:start:python:dpe'

        res = manager.dispatch_request(msg)

        mock_sc.assert_called_once_with('python', 'dpe')
        self.assertSequenceEqual(res, ['SUCCESS', ''])

    @mock.patch('clara_manager.ClaraManager.stop_clara')
    def test_dispatch_stop_request(self, mock_sc):
        manager = ClaraManager(clara)
        msg = 'clara:stop:python:dpe'

        res = manager.dispatch_request(msg)

        mock_sc.assert_called_once_with('python', 'dpe')
        self.assertSequenceEqual(res, ['SUCCESS', ''])

    @mock.patch('clara_manager.ClaraManager.start_clara')
    def test_dispatch_request_start_raises(self, mock_sc):
        manager = ClaraManager(clara)
        msg = 'clara:start:python:monitor'
        mock_sc.side_effect = ClaraManagerError('Bad instance: monitor')

        res = manager.dispatch_request(msg)

        self.assertSequenceEqual(res, ['ERROR', 'Bad instance: monitor'])

    @mock.patch('clara_manager.ClaraManager.start_clara')
    def test_dispatch_request_start_unexpected_problem(self, mock_sc):
        manager = ClaraManager(clara)
        msg = 'clara:start:python:dpe'
        mock_sc.side_effect = OSError('Popen error')

        res = manager.dispatch_request(msg)

        self.assertSequenceEqual(res, ['ERROR',
                                       'Unexpected exception: Popen error'])

    @mock.patch('clara_manager.ClaraManager.stop_clara')
    def test_dispatch_request_stop_raises(self, mock_sc):
        manager = ClaraManager(clara)
        msg = 'clara:stop:python:monitor'
        mock_sc.side_effect = ClaraManagerError('Bad instance: monitor')

        res = manager.dispatch_request(msg)

        self.assertSequenceEqual(res, ['ERROR', 'Bad instance: monitor'])

if __name__ == '__main__':
    unittest.main()
