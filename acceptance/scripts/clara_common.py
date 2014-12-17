import os
import yaml


def get_base_dir():
    cwd = os.getcwd()
    base_cwd = os.path.basename(cwd)
    if base_cwd == 'scripts':
        return '..'
    elif base_cwd == 'acceptance' or base_cwd == 'vagrant':
        return '.'
    else:
        raise RuntimeError("Run from the 'acceptance (or vagrant)' directory")


def read_yaml(yaml_file):
    with open(yaml_file) as f:
        return yaml.load(f)


def get_config_file(base_dir):
    return os.path.join(base_dir, 'default-config.yaml')


def get_config_section(config_file, key):
    data = read_yaml(config_file)
    section = data.get(key)
    if not section:
        raise RuntimeError('Bad config file: missing %s' % key)
    return section
