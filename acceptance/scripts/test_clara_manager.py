import unittest
import mock
import os
import subprocess
import zmq

from clara_manager import ClaraManager
from clara_manager import ClaraManagerError
from clara_manager import ClaraProcessConfig
from clara_manager import stop_process
from clara_manager import stop_all
from clara_manager import host_ip
from clara_manager import __name__ as cm

from test_clara_testing import patch_on_setup

clara = {
    'logs': '/clara/logs',
    'python': {
        'fullpath': '/clara/python',
        'platform': 'python -u core/system/Platform.py',
        'dpe': 'python -u core/system/Dpe.py',
    },
    'java': {
        'fullpath': '/clara/services',
        'platform': './bin/clara-platform',
        'dpe': './bin/clara-dpe -p platform',
        'orchestrator': './bin/standard-orchestrator',
    },
}


class TestClaraProcessConfig(unittest.TestCase):

    def test_clara_python_config(self):
        wd = '/clara/python'
        cmd = ['python', '-u', 'core/system/Platform.py']

        with mock.patch.dict(os.environ, clear=True):
            env = {'PYTHONPATH': '/clara/python'}
            self._assert_clara_config('python', 'platform', cmd, wd, env)

        with mock.patch.dict(os.environ, {'PYTHONPATH': '/opt/python'}):
            env = dict(os.environ, PYTHONPATH='/clara/python:/opt/python')
            self._assert_clara_config('python', 'platform', cmd, wd, env)

    def test_clara_java_config(self):
        with mock.patch.dict(os.environ, clear=True):
            wd = '/clara/services'
            cmd = ['./bin/clara-dpe', '-p', 'platform']
            env = {'CLARA_SERVICES': '/clara/services'}
            self._assert_clara_config('java', 'dpe', cmd, wd, env)

    def test_standard_request_config(self):
        conf = ClaraProcessConfig(clara, 'java', 'orchestrator')
        self.assertEqual(conf.cmd, ['./bin/standard-orchestrator'])

    def _assert_clara_config(self, lang, instance, command, working_dir,
                             env=os.environ):
        conf = ClaraProcessConfig(clara, lang, instance)

        self.assertEqual(conf.cmd, command)
        self.assertEqual(conf.cwd, working_dir)
        self.assertEqual(conf.env, env)

    def test_open_logs(self):
        out_log = "/clara/logs/%s-%s-%s.log" % (host_ip, 'java', 'dpe')
        err_log = "/clara/logs/%s-%s-%s.err" % (host_ip, 'java', 'dpe')
        conf = ClaraProcessConfig(clara, 'java', 'dpe')

        with mock.patch('%s.open' % cm, mock.mock_open(), create=True) as o:

            o.side_effect = lambda *args: args[0]

            conf.open_logs()

            log_calls = [mock.call(out_log, 'w+'), mock.call(err_log, 'w+')]
            o.assert_has_calls(log_calls)

            self.assertEqual(conf.out, out_log)
            self.assertEqual(conf.err, err_log)

    def test_close_logs(self):
        with mock.patch('%s.open' % cm, mock.mock_open(), create=True) as o:
            out_mock = mock.Mock()
            err_mock = mock.Mock()

            o.side_effect = [out_mock, err_mock]

            conf = ClaraProcessConfig(clara, 'java', 'dpe')
            conf.open_logs()
            conf.close_logs()

            out_mock.close.assert_called_with()
            err_mock.close.assert_called_with()

            self.assertEqual(conf.out, None)
            self.assertEqual(conf.err, None)


class TestClaraManagerStart(unittest.TestCase):

    def setUp(self):
        self.manager = ClaraManager(clara)

        self.mock_t = patch_on_setup(self, 'time.sleep')
        self.mock_po = patch_on_setup(self, 'subprocess.Popen')
        self.mock_cc = patch_on_setup(self, 'clara_manager.ClaraProcessConfig')

        self.ps = self.mock_po.return_value
        self.cc = self.mock_cc.return_value

        self.ps.poll.return_value = None

    def test_start_clara_raises_on_bad_instance(self):
        self.assertRaisesRegexp(ClaraManagerError, 'Bad instance: monitor',
                                self.manager.start_clara, 'python', 'monitor')

    def test_start_clara_raises_on_bad_lang(self):
        self.assertRaisesRegexp(ClaraManagerError, 'Bad language: erlang',
                                self.manager.start_clara, 'erlang', 'dpe')

    def test_start_clara_raises_if_already_running(self):
        self.manager.instances = {'python/dpe': None}
        self.assertRaisesRegexp(ClaraManagerError, 'python/dpe already run',
                                self.manager.start_clara, 'python', 'dpe')

    def test_start_clara_creates_config(self):
        self.manager.start_clara('python', 'dpe')

        self.mock_cc.assert_called_once_with(clara, 'python', 'dpe')

    def test_start_clara_open_logs(self):
        self.manager.start_clara('python', 'dpe')

        self.cc.open_logs.assert_called_once_with()
        self.assertFalse(self.cc.close_logs.called)

    def test_start_clara_run_process(self):
        self.manager.start_clara('python', 'dpe')

        cc = mock_cc.return_value
        mock_ps.assert_called_once_with(cc.cmd,
                                        env=cc.env,
                                        cwd=cc.cwd,
                                        preexec_fn=os.setsid,
                                        stdout=cc.out,
                                        stderr=cc.err)

    def test_start_clara_store_process(self):
        self.manager.start_clara('python', 'platform')

        self.cc.set_proc.assert_called_once_with(self.ps)

    def test_start_clara_store_config(self):
        self.manager.start_clara('python', 'platform')

        key = 'python/platform'
        self.assertIn(key, self.manager.instances)

        clara_run = self.manager.instances[key]
        self.assertEquals(clara_run, self.cc)

    def test_start_clara_dont_store_config_on_process_error(self):
        self.ps.poll.return_value = 1
        try:
            self.manager.start_clara('python', 'platform')
        except:
            pass
        self.assertNotIn('python/platform', self.manager.instances)

    def test_start_clara_raises_on_process_error(self):
        self.ps.poll.return_value = 1

        self.assertRaisesRegexp(ClaraManagerError,
                                'Could not start python/platform',
                                self.manager.start_clara,
                                'python', 'platform')

    def test_start_clara_close_logs_on_process_error(self):
        self.ps.poll.return_value = 1
        try:
            self.manager.start_clara('python', 'platform')
        except:
            pass
        self.cc.close_logs.assert_called_once_with()


class TestClaraManagerStop(unittest.TestCase):

    def test_stop_clara_raises_on_bad_instance(self):
        manager = ClaraManager(clara)

        self.assertRaisesRegexp(ClaraManagerError, 'Bad instance: monitor',
                                manager.stop_clara, 'python', 'monitor')

    def test_stop_clara_raises_on_bad_lang(self):
        manager = ClaraManager(clara)

        self.assertRaisesRegexp(ClaraManagerError, 'Bad language: erlang',
                                manager.stop_clara, 'erlang', 'dpe')

    def test_stop_clara_raises_if_not_running(self):
        manager = ClaraManager(clara)

        self.assertRaisesRegexp(ClaraManagerError, 'python/dpe is not run',
                                manager.stop_clara, 'python', 'dpe')

    @mock.patch('clara_manager.stop_process')
    def test_stop_clara_stops_process(self, mock_stop):
        run1 = ClaraProcessConfig(clara)
        run2 = ClaraProcessConfig(clara)
        run3 = ClaraProcessConfig(clara)
        manager = ClaraManager(clara)
        manager.instances = {
            'python/dpe': run1, 'python/platform': run2, 'java/dpe': run3
        }
        result = {'python/platform': run2, 'java/dpe': run3}

        manager.stop_clara('python', 'dpe')

        mock_stop.assert_called_once_with(run1)
        self.assertDictEqual(manager.instances, result)


class TestStopProcess(unittest.TestCase):

    @mock.patch('psutil.Process')
    def test_stop_process_terminates_the_process(self, mock_ps):
        proc = mock_ps.return_value
        conf = mock.Mock()
        conf.proc = proc

        proc.is_running.return_value = False
        proc.get_children.return_value = []
        stop_process(conf)

        proc.terminate.assert_called_once_with()
        self.assertTrue(not proc.kill.called)

    @mock.patch('time.sleep')
    @mock.patch('psutil.Process')
    def test_stop_process_with_forced_kill(self, mock_ps, mock_t):
        proc = mock_ps.return_value
        conf = mock.Mock()
        conf.proc = proc

        proc.is_running.return_value = True
        proc.get_children.return_value = []

        self.assertRaises(OSError, stop_process, conf)

        proc.kill.assert_called_once_with()
        proc.wait.assert_called_once_with()

    @mock.patch('psutil.Process')
    def test_stop_process_close_logs(self, mock_ps):
        proc = mock_ps.return_value
        conf = mock.Mock()
        conf.proc = proc

        proc.is_running.return_value = False
        proc.get_children.return_value = []

        stop_process(conf)

        conf.close_logs.assert_called_once_with()

    @mock.patch('psutil.Process')
    def test_stop_process_stop_all_children(self, mock_ps):
        proc = mock_ps.return_value
        conf = mock.Mock()
        conf.proc = proc

        proc.is_running.return_value = False
        proc.get_children.return_value = [proc] * 2

        stop_process(conf)

        self.assertEqual(proc.terminate.call_count, 2)

    @mock.patch('time.sleep')
    def test_stop_process_force_children_kill(self, mock_t):
        with mock.patch('psutil.Process') as mock_bp, \
                mock.patch('psutil.Process') as mock_ps:
            bad_proc = mock_bp.return_value
            proc = mock_ps.return_value

            bad_proc.is_running.return_value = True
            proc.is_running.return_value = False

            proc.get_children.return_value = [bad_proc]

            conf = mock.Mock()
            conf.proc = proc

            self.assertRaises(OSError, stop_process, conf)

            bad_proc.kill.assert_called_once_with()
            bad_proc.wait.assert_called_once_with()

            self.assertFalse(proc.terminate.called)

    @mock.patch('clara_manager.stop_process')
    def test_stop_all_processes(self, mock_sp):
        manager = ClaraManager(clara)
        manager.instances = {'p/d': 'p1', 'p/p': 'p2', 'j/d': 'p3'}

        stop_all(manager)

        mock_sp.assert_any_call('p1')
        mock_sp.assert_any_call('p2')
        mock_sp.assert_any_call('p3')
        self.assertEqual(mock_sp.call_count, 3)
        self.assertTrue(not manager.instances)

    @mock.patch('clara_manager.stop_process')
    def test_stop_all_processes_with_forced_kill(self, mock_sp):
        manager = ClaraManager(clara)
        manager.instances = {'p/d': 'p1', 'p/p': 'p2', 'j/d': 'p3'}

        mock_sp.side_effect = OSError

        stop_all(manager)

        mock_sp.assert_any_call('p1')
        mock_sp.assert_any_call('p2')
        mock_sp.assert_any_call('p3')
        self.assertEqual(mock_sp.call_count, 3)
        self.assertTrue(not manager.instances)


class TestClaraManagerDispatch(unittest.TestCase):

    @mock.patch('zmq.Socket')
    @mock.patch('zmq.Context')
    @mock.patch('time.sleep')
    def test_zmq_server_is_up(self, mock_t, mock_ctx, mock_sck):
        manager = ClaraManager(clara)

        ctx = mock_ctx.return_value
        sck = mock_sck.return_value

        ctx.socket.return_value = sck
        sck.recv.side_effect = NotImplementedError

        self.assertRaises(NotImplementedError, manager.run)

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

        self.assertRaises(NotImplementedError, manager.run)

        sck.recv.assert_called_once_with()
        mock_dr.assert_called_once_with(msg)
        sck.send_multipart.assert_called_once_with(res)

    def test_dispatch_returns_error_if_empty_request(self):
        manager = ClaraManager(clara)
        msg = ''

        res = manager.dispatch_request(msg)

        self.assertSequenceEqual(res, ['ERROR', 'Empty request'])

    def test_dispatch_returns_error_if_bad_request(self):
        manager = ClaraManager(clara)
        msg = 'clara:start'

        res = manager.dispatch_request(msg)

        self.assertSequenceEqual(res, ['ERROR', 'Bad request: "clara:start"'])

    def test_dispatch_returns_error_if_bad_action(self):
        manager = ClaraManager(clara)
        msg = 'clara:launch:python:dpe'

        res = manager.dispatch_request(msg)

        self.assertSequenceEqual(res, ['ERROR', 'Unsupported action: launch'])

    @mock.patch('clara_manager.ClaraManager.start_clara')
    def test_dispatch_successful_start_request(self, mock_sc):
        manager = ClaraManager(clara)
        msg = 'clara:start:python:dpe'

        res = manager.dispatch_request(msg)

        mock_sc.assert_called_once_with('python', 'dpe')
        self.assertSequenceEqual(res, ['SUCCESS', ''])

    @mock.patch('clara_manager.ClaraManager.stop_clara')
    def test_dispatch_successful_stop_request(self, mock_sc):
        manager = ClaraManager(clara)
        msg = 'clara:stop:python:dpe'

        res = manager.dispatch_request(msg)

        mock_sc.assert_called_once_with('python', 'dpe')
        self.assertSequenceEqual(res, ['SUCCESS', ''])

    @mock.patch('clara_manager.ClaraManager.standard_request')
    def test_dispatch_successful_standard_request(self, mock_sr):
        manager = ClaraManager(clara)
        msg = 'clara:request:java:list-dpes'
        mock_sr.return_value = ['OK'], [''], 0

        res = manager.dispatch_request(msg)

        mock_sr.assert_called_once_with('java', 'list-dpes')
        self.assertSequenceEqual(res, ['SUCCESS', 'OK'])

    @mock.patch('clara_manager.stop_all')
    def test_dispatch_sucessful_stop_all_request(self, mock_sa):
        manager = ClaraManager(clara)
        msg = 'clara:stop:all:all'

        res = manager.dispatch_request(msg)

        mock_sa.assert_called_once_with(manager)
        self.assertSequenceEqual(res, ['SUCCESS', ''])
        self.assertTrue(not manager.instances)

    @mock.patch('clara_manager.ClaraManager.stop_clara')
    def test_dispatch_returns_error_if_request_failed(self, mock_sc):
        manager = ClaraManager(clara)
        msg = 'clara:start:python:monitor'
        mock_sc.side_effect = ClaraManagerError('Bad instance: monitor')

        res = manager.dispatch_request(msg)

        self.assertSequenceEqual(res, ['ERROR', 'Bad instance: monitor'])

    @mock.patch('clara_manager.ClaraManager.start_clara')
    def test_dispatch_returns_error_on_request_error(self, mock_sc):
        manager = ClaraManager(clara)
        msg = 'clara:start:python:dpe'
        mock_sc.side_effect = OSError('Popen error')

        res = manager.dispatch_request(msg)

        self.assertSequenceEqual(res, ['ERROR',
                                       'Unexpected exception: Popen error'])

    @mock.patch('clara_manager.ClaraManager.standard_request')
    def test_dispatch_returns_error_if_standard_request_failed(self, mock_sr):
        manager = ClaraManager(clara)
        msg = 'clara:request:java:list-dpes'
        mock_sr.return_value = ['OUT1', 'OUT2'], ['ERR'], 1

        res = manager.dispatch_request(msg)

        self.assertSequenceEqual(res, ['ERROR', 'OUT1', 'OUT2', 'ERR'])


class TestClaraManagerStandardRequest(unittest.TestCase):

    def setUp(self):
        self.manager = ClaraManager(clara)

    def test_standard_request_raises_on_bad_language(self):

        self.assertRaisesRegexp(ClaraManagerError, 'Bad language: erlang',
                                self.manager.standard_request,
                                'erlang', 'list-dpes')

    @mock.patch('subprocess.Popen')
    @mock.patch('clara_manager.ClaraProcessConfig')
    def test_standard_request_creates_config(self, mock_cc, mock_po):
        mock_po.return_value.communicate.return_value = '', ''

        self.manager.standard_request('java', 'list-dpes')

        mock_cc.assert_called_once_with(clara, 'java', 'orchestrator')

    @mock.patch('subprocess.Popen')
    @mock.patch('clara_manager.ClaraProcessConfig')
    def test_start_clara_run_process(self, mock_cc, mock_po):
        mock_po.return_value.communicate.return_value = '', ''
        cc = mock_cc.return_value
        cc.cmd = ['./bin/std-orch']

        self.manager.standard_request('java', 'list-dpes')

        mock_po.assert_called_once_with(['./bin/std-orch', 'list-dpes'],
                                        env=cc.env,
                                        cwd=cc.cwd,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)

    @mock.patch('subprocess.Popen')
    @mock.patch('clara_manager.ClaraProcessConfig')
    def test_start_clara_gets_process_ouput(self, mock_cc, mock_po):
        mock_po.return_value.communicate.return_value = 'OUT\nALL\n', ''
        mock_po.return_value.returncode = 0

        out, err, rc = self.manager.standard_request('java', 'list-dpes')

        self.assertEqual(out, ['OUT', 'ALL'])
        self.assertEqual(err, [])
        self.assertEqual(rc, 0)


if __name__ == '__main__':
    unittest.main()
