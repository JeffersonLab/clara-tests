# Clara Acceptance Tests

Test Clara messaging using a local mini cloud of virtual machines.

## Dependencies

- Install [Virtualbox](https://www.virtualbox.org/)
- Install [Vagrant](https://www.vagrantup.com/) (1.4+)

### Optional

- Install [vagrant-cachier](https://github.com/fgrehm/vagrant-cachier) to
  cache the packages installed when the nodes are provisioned.

## Clara sources

The different Clara sources should be in the same directory.
This directory will be mounted as a synced folder in every virtual machine.

The default configuration sets this to `../..` (i.e. relative to this
`acceptance` directory) and expects specific names for each Clara version:

    $ pwd
    /home/user/dev/clara-tests/acceptance

    $ ls ../..
    clara-cpp  clara-java  clara-python  clara-tests  clara-webapp

To use your own paths, copy the file `default-config.yaml` to
`custom-config.yaml`, and you can change the common source directory and the
names of the directories for each project.

## Start nodes

To start the cluster of nodes, run the following:

    $ vagrant up

## Run Tests

TODO.
