import mock
import unittest
import zmq

from clara_testing import ClaraRequestError
from clara_testing import ClaraDaemonClient


nodes = {
    'platform': '10.11.1.100',
    'dpe1': '10.11.1.101',
    'dpe2': '10.11.1.102',
}


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


if __name__ == '__main__':
    unittest.main()