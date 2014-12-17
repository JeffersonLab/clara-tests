import mock
import unittest

from clara_common import get_config_file
from clara_common import get_base_dir
from clara_common import get_config_section

nodes = {
    'platform': '10.11.1.100',
    'dpe1': '10.11.1.101',
    'dpe2': '10.11.1.102',
}


class TestCommonUtils(unittest.TestCase):

    @mock.patch('os.getcwd')
    def test_get_base_dir(self, mock_cwd):
        mock_cwd.return_value = '/home/user/dev/clara-test/acceptance/scripts'
        self.assertEqual(get_base_dir(), '..')

        mock_cwd.return_value = '/home/user/dev/clara-test/acceptance'
        self.assertEqual(get_base_dir(), '.')

        mock_cwd.return_value = '/vagrant/scripts'
        self.assertEqual(get_base_dir(), '..')

        mock_cwd.return_value = '/vagrant'
        self.assertEqual(get_base_dir(), '.')

    @mock.patch('os.getcwd')
    def test_get_base_dir_raises_if_wrong_current_directory(self, mock_cwd):
        mock_cwd.return_value = '/home/user/dev/'
        self.assertRaisesRegexp(RuntimeError, 'Run from', get_base_dir)

    def test_get_config_file(self):
        self.assertEqual(get_config_file('.'), './default-config.yaml')

    @mock.patch('clara_common.read_yaml')
    def test_get_config_section(self, mock_ry):
        mock_ry.return_value = {'nodes': nodes}

        self.assertEqual(get_config_section('.', 'nodes'), nodes)

    @mock.patch('clara_common.read_yaml')
    def test_get_config_section_reads_config_file(self, mock_ry):
        get_config_section('./config.yaml', 'projects')

        mock_ry.assert_called_once_with('./config.yaml')

    @mock.patch('clara_common.read_yaml')
    def test_get_config_section_raises_if_missing_nodes(self, mock_ry):
        mock_ry.return_value = {}

        self.assertRaisesRegexp(RuntimeError, 'missing nodes',
                                get_config_section, '.', 'nodes')


if __name__ == '__main__':
    unittest.main()
