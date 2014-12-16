# Clara Acceptance Tests

Test Clara messaging using a local mini cloud of virtual machines.

## Dependencies

- Install [Virtualbox](https://www.virtualbox.org/)
- Install [Vagrant](https://www.vagrantup.com/) (1.4+)

### Optional

- Install [vagrant-cachier](https://github.com/fgrehm/vagrant-cachier) to
  cache the packages installed when the nodes are provisioned.


## xMsg and Clara sources

The different xMsg and Clara sources should be in the same directory.
This directory will be mounted as a synced folder in every virtual machine.

The default configuration sets this to `../..` (i.e. relative to this
`acceptance` directory) and expects specific names for each xMsg and Clara
version:

    $ pwd
    /home/user/dev/clara-tests/acceptance

    $ ls ../..
    clara-cpp  clara-java  clara-python  clara-tests  clara-webapp
    xmsg-cpp   xmsg-java   xmsg-python

To use your own paths, copy the file `default-config.yaml` to
`custom-config.yaml`, and you can change the common source directory and the
names of the directories for each project.


## Start nodes

To start the cluster of nodes, run the following:

    $ vagrant up

Or to start a single node, pass the node name:

    $ vagrant up platform

The first time, the virtual machines will be created and provisioned with all
the dependencies and files needed for development and testing (this may take
several minutes).
As the configuration evolves, you will need to re-provision the machines to
keep them up to date:

    $ vagrant provision

To access the machines, do:

    $ vagrant ssh <node>

See the [Vagrant docs][vd] for advanced usage.

[vd]: https://docs.vagrantup.com/v2/getting-started/index.html


## Run Tests

Once all the machines are up and provisioned, launch all the tests with:

    $ ./run
