import mock
import unittest
import zmq

from clara_testing import ClaraRequestError
from clara_testing import ClaraDaemonClient
from clara_testing import ClaraTest
from clara_testing import ClaraTestSuite
from clara_testing import ClaraTestRunner

from clara_testing import get_all_files
from clara_testing import parse_action

from test_clara_common import nodes


def patch_on_setup(instance, name):
    patcher = mock.patch(name)
    mock_obj = patcher.start()
    instance.addCleanup(patcher.stop)
    return mock_obj


class TestClaraDaemonClient(unittest.TestCase):

    def setUp(self):
        mock_ctx = patch_on_setup(self, 'zmq.Context')
        mock_sck = patch_on_setup(self, 'zmq.Socket')

        self.ctx = mock_ctx.return_value
        self.sck = mock_sck.return_value

        self.ctx.socket.return_value = self.sck

        self.client = ClaraDaemonClient(self.ctx, nodes)

    def test_connect_socket(self):
        n_nodes = len(nodes)
        ip_nodes = nodes.values()

        ctx_socket_calls = [mock.call(zmq.REQ)] * n_nodes
        sck_connect_calls = [mock.call("tcp://%s:7788" % i) for i in ip_nodes]

        self.ctx.socket.assert_has_calls(ctx_socket_calls)
        self.sck.connect.assert_has_calls(sck_connect_calls, any_order=True)

        self.assertEqual(self.ctx.socket.call_count, n_nodes)
        self.assertEqual(self.sck.connect.call_count, n_nodes)

    def test_request_sends_and_receives_response(self):
        self.sck.recv_multipart.return_value = ['SUCCESS', 'One', 'Two']

        msg = 'clara:start:python:dpe'
        text = self.client.request('platform', msg)

        self.sck.send.assert_called_once_with(msg)
        self.sck.recv_multipart.assert_called_once_with()

        self.assertEqual(text, ['One', 'Two'])

    def test_request_throws_if_bad_node(self):
        self._assert_request_exception('bad_node',
                                       'clara:start:python:dpe',
                                       'Bad node: "bad_node"')

    def test_request_throws_if_empty_message(self):
        self._assert_request_exception('platform',
                                       '',
                                       'Empty message')

    def test_request_throws_if_empty_response(self):
        self._test_request_response('',
                                    "Empty response")

    def test_request_throws_if_missing_response_text(self):
        self._test_request_response(['SUCCESS'],
                                    "Bad response: \"['SUCCESS']\"")

    def test_request_throws_if_status_is_error(self):
        self._test_request_response(['ERROR', 'Problem:', 'reason'],
                                    "Problem:\nreason")

    def test_request_throws_if_missing_error_message(self):
        self._test_request_response(['ERROR', ''],
                                    "Empty error")

    def test_request_throws_if_bad_status(self):
        self._test_request_response(['SOMETHING', 'Text'],
                                    'Bad status: "SOMETHING"')

    @mock.patch('clara_testing.ClaraDaemonClient._request')
    def test_request_all(self, mock_rq):
        msg = 'clara:stop:all:all'
        n_nodes = len(nodes)

        request_calls = [mock.call(self.sck, msg)] * n_nodes

        self.client.request_all(msg)

        mock_rq.assert_has_calls(request_calls)
        self.assertEqual(mock_rq.call_count, n_nodes)

    def _assert_request_exception(self, node, msg, err_msg):
        with self.assertRaises(ClaraRequestError) as e:
            self.client.request(node, msg)
        self.assertEquals(str(e.exception), err_msg)

    def _test_request_response(self, recv_resp, err_msg):
        self.sck.recv_multipart.return_value = recv_resp
        self._assert_request_exception('dpe1', 'clara:start:java:dpe', err_msg)


class TestClaraTest(unittest.TestCase):
    def setUp(self):
        mock_cd = patch_on_setup(self, 'clara_testing.ClaraDaemonClient')
        mock_pa = patch_on_setup(self, 'clara_testing.parse_action')

        self.client = mock_cd.return_value
        self.parser = mock_pa

        self.actions = ['1', '2', '3']
        self.result = ['R']
        self.data = {'actions': self.actions, 'result': self.result}
        self.item = 'J'

        self.client.request.return_value = self.result
        self.parser.return_value = (None, None)

    def test_parse_all_actions(self):
        calls = [mock.call(a, self.item) for a in self.data['actions']]

        ClaraTest(self.client, self.data, self.item).run()

        self.parser.assert_has_calls(calls)
        self.assertEqual(self.parser.call_count, len(calls))

    def test_request_all_actions(self):
        parsed = [('node', a) for a in self.data['actions']]
        calls = [mock.call(*p) for p in parsed]

        self.parser.side_effect = parsed

        ClaraTest(self.client, self.data, self.item).run()

        self.client.request.assert_has_calls(calls)
        self.assertEqual(self.client.request.call_count, len(calls))

    def test_run_using_result_of_last_action(self):
        self._assert_result((['A'], ['B'], ['C', 'D']), ['C', 'D'])

    def test_request_test_with_empty_result(self):
        self._assert_result((['A'], ['B'], []), [])

    def test_raise_if_last_action_returns_wrong_result(self):
        self.data.update({'result': ['M', 'A']})
        results = (['A', 'B'], ['C'], ['D', 'E'])

        self.client.request.side_effect = results
        regex = "Wrong result:.*'D', 'E'.*Expected:.*'M', 'A'"

        self._assert_run_exception(regex)

    def test_raise_if_no_actions_in_data(self):
        del self.data['actions']
        self._assert_run_exception("no actions")

    def test_raise_if_no_result_in_data(self):
        del self.data['result']
        self._assert_run_exception("no result")

    def test_propagate_parse_exception(self):
        self.parser.side_effect = ClaraRequestError("Parse error")
        self._assert_run_exception("Parse error")

    def test_propagate_request_exception(self):
        self.client.request.side_effect = ClaraRequestError("Request error")
        self._assert_run_exception("Request error")

    def _assert_result(self, action_results, result):
        self.data.update({'result': result})

        self.client.request.side_effect = action_results
        test = ClaraTest(self.client, self.data, self.item)

        self.assertEqual(test.run(), result)

    def _assert_run_exception(self, regex, exc=ClaraRequestError):
        test = ClaraTest(self.client, self.data, self.item)
        self.assertRaisesRegexp(exc, regex, test.run)


class TestClaraTestSuite(unittest.TestCase):

    def setUp(self):
        self.mock_cd = patch_on_setup(self, 'clara_testing.ClaraDaemonClient')
        self.mock_ry = patch_on_setup(self, 'clara_testing.read_yaml')
        self.mock_ct = patch_on_setup(self, 'clara_testing.ClaraTest')

    def _create_suite(self, data, test_file='./test.yaml'):
        self.mock_ry.return_value = data
        return ClaraTestSuite(self.mock_cd.return_value, test_file)

    def test_read_data_from_file(self):
        data = {'tests': ['1']}
        name = './10_test_msg.yaml'

        self._create_suite(data, name)

        self.mock_ry.assert_called_once_with(name)

    def test_run_all_tests_in_file_with_no_items(self):
        data = {'tests': ['1', '2', '3']}
        tests = [(t, 'java') for t in data['tests']]

        self._assert_run_all_tests(data, tests)

    def test_run_all_tests_in_file_for_each_item(self):
        data = {'tests': ['1', '2', '3'], 'with': ['J', 'P']}
        tests = [(t, i) for i in data['with'] for t in data['tests']]

        self._assert_run_all_tests(data, tests)

    def _assert_run_all_tests(self, test_data, exp_tests):
        def set_status(*args):
            act_tests.append((args[1], args[2]))
            return mock.DEFAULT

        act_tests = []
        self.mock_ct.side_effect = set_status

        self._create_suite(test_data).run_tests()

        self.assertEqual(act_tests, exp_tests)
        self.assertEqual(self.mock_ct.return_value.run.call_count,
                         len(exp_tests))

    def test_dont_run_remaining_tests_on_error(self):
        data = {'tests': ['1', '2', '3']}
        it = iter(data['tests'])

        def raise_error(*args):
            if next(it) == '2':
                raise ClaraRequestError

        run = self.mock_ct.return_value.run
        run.side_effect = raise_error

        self._create_suite(data).run_tests()

        self.assertEqual(run.call_count, 2)

    def test_use_filename_if_no_name(self):
        data = {'tests': ['1']}

        suite = self._create_suite(data, './01_my_name.yaml')

        self.assertEqual(suite.run_tests()[1], '01_my_name')

    def test_return_success_if_all_tests_passed(self):
        data = {'name': 'NAME', 'tests': ['1']}

        suite = self._create_suite(data)

        self.assertEqual(suite.run_tests(), (True, 'NAME'))

    def test_return_error_on_failed_test(self):
        data = {'name': 'NAME', 'tests': ['1']}

        test = self.mock_ct.return_value
        test.run.side_effect = ClaraRequestError

        suite = self._create_suite(data)

        self.assertEqual(suite.run_tests(), (False, 'NAME'))

    def test_return_error_if_no_tests(self):
        data = {'name': 'NAME'}

        suite = self._create_suite(data)

        self.assertEqual(suite.run_tests(), (False, 'NAME'))

    def test_return_error_if_empty_tests(self):
        data = {'name': 'NAME', 'tests': []}

        suite = self._create_suite(data)

        self.assertEqual(suite.run_tests(), (False, 'NAME'))

    def test_stop_all_clara_instances_on_success(self):
        data = {'tests': ['1', '2', '3']}
        client = self.mock_cd.return_value

        self._create_suite(data).run_tests()

        client.request_all.assert_called_once_with('clara:stop:all:all')

    def test_stop_all_clara_instances_on_error(self):
        data = {'tests': ['1', '2', '3']}
        client = self.mock_cd.return_value
        test = self.mock_ct.return_value

        test.run.side_effect = ClaraRequestError

        self._create_suite(data).run_tests()

        client.request_all.assert_called_once_with('clara:stop:all:all')

    def test_dont_send_stop_requests_if_no_tests(self):
        data = {'name': 'NAME'}
        client = self.mock_cd.return_value

        self._create_suite(data).run_tests()

        self.assertFalse(client.request_all.called)


class TestClaraTestRunner(unittest.TestCase):

    def setUp(self):
        self.mock_ctx = patch_on_setup(self, 'zmq.Context')
        self.mock_cln = patch_on_setup(self, 'clara_testing.ClaraDaemonClient')

        self.test_files = ['./t/01.yaml', './t/02.yaml', './t/05.yaml']
        self.runner = ClaraTestRunner(nodes, self.test_files)

    def test_start_client(self):
        self.runner.start_client()

        ctx = self.mock_ctx.return_value
        self.mock_cln.assert_called_once_with(ctx, nodes)

    @mock.patch('clara_testing.ClaraTestSuite')
    def test_run_all_files(self, mock_cts):
        def set_status(*args):
            test_suites.append(args[1])
            return mock.DEFAULT

        test_suites = []
        mock_cts.side_effect = set_status

        self.runner.run_all_tests()

        self.assertEqual(test_suites, self.test_files)

    @mock.patch('clara_testing.ClaraTestSuite')
    def test_report_all_tests(self, mock_cts):
        mock_cts.return_value.run_tests.side_effect = self.test_files

        result = self.runner.run_all_tests()

        self.assertEqual(result, self.test_files)


class TestUtils(unittest.TestCase):

    @mock.patch('os.listdir')
    def test_get_all_files(self, mock_ls):
        mock_ls.return_value = ['01-run.yaml', '02-dpes.yaml', 'dummmy']

        self.assertEqual(get_all_files('.'),
                         ['./tests/01-run.yaml', './tests/02-dpes.yaml'])

    def test_parse_action_replace_item(self):
        self.assertEqual(parse_action('start {{item}} platform', 'python'),
                         ('platform', 'clara:start:python:platform'))

        self.assertRaisesRegexp(ClaraRequestError,
                                'Malformed action: "start cpp dpe"',
                                parse_action, 'start {{item}} dpe', 'cpp')

    def test_parse_action_for_platform(self):
        self.assertEqual(parse_action('start platform'),
                         ('platform', 'clara:start:java:platform'))

        self.assertEqual(parse_action('stop  python platform', 'java'),
                         ('platform', 'clara:stop:python:platform'))

        self.assertRaises(ClaraRequestError, parse_action, 'start a platform')
        self.assertRaises(ClaraRequestError, parse_action, 'launch platform')

    def test_parse_action_for_dpe(self):
        self.assertEqual(parse_action('start {{item}} dpe on dpe1', 'python'),
                         ('dpe1', 'clara:start:python:dpe'))

        self.assertEqual(parse_action('stop java dpe on dpe1'),
                         ('dpe1', 'clara:stop:java:dpe'))

        self.assertRaises(ClaraRequestError, parse_action, 'start dpe on node')

    def test_parse_action_for_standard_requests(self):
        self.assertEqual(parse_action('request list dpes'),
                         ('platform', 'clara:request:java:list-dpes'))

        self.assertEqual(parse_action('request python  list  dpes on dpe2'),
                         ('dpe2', 'clara:request:python:list-dpes'))

        self.assertRaises(ClaraRequestError, parse_action, 'request all dpes')


if __name__ == '__main__':
    unittest.main()
