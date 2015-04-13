# Clara Acceptance Tests

Test Clara messaging using a local mini cloud of virtual machines.

## Dependencies

- Install [Virtualbox](https://www.virtualbox.org/)
- Install [Vagrant](https://www.vagrantup.com/) (1.4+)

### Optional

- Install [vagrant-cachier](https://github.com/fgrehm/vagrant-cachier) to
  cache the packages installed when the nodes are provisioned.


## Quick Run

To create the virtual machines, download and install Clara, and run all tests,
do:

    $ vagrant up
    $ ./install
    $ ./run

Read below for full instructions.

## Creating the Virtual Machines

To start the cluster of nodes, run the following:

    $ vagrant up

Or, to start a single node, pass the node name (but all the nodes must be up
in order to run the tests):

    $ vagrant up platform

The first time, the virtual machines will be created and **provisioned** with
all the dependencies and files needed for development and testing (this may
take several minutes).
As the configuration evolves, you will need to re-provision the machines to
keep them up to date:

    $ vagrant provision

To access the machines, do:

    $ vagrant ssh <node>

See the [Vagrant docs][vd] for advanced usage.

[vd]: https://docs.vagrantup.com/v2/getting-started/index.html


## Installing Clara

The different Clara sources and dependencies should be in the same directory,
because that directory will be mounted as a synced folder in every virtual
machine.

The default configuration sets this to `../..` (i.e. the directory where this
project is located), and uses specific names for each project:

    $ pwd
    /home/user/dev/clara-tests/acceptance

    $ ls ../..
    clara-cpp  clara-java  clara-tests  clara-webapp  ctoolbox  jtoolbox

The `$CLARA_HOME` directory is also a shared folder, common to all the
machines. This directory is created when the machines are provisioned:

    $ ls services
    log

To simplify the installation of all the projects, an installer is provided.
With the virtual machines already provisioned, run:

    $ ./install

This script will _checkout_, _build_ and _install_ every project,
using the settings in the distributed configuration file.
The projects can also be manually downloaded,
since the installer will not overwrite a project that is already present
(i.e. only if the project directory is named as expected by the script).

To customize the paths and build instructions of the installer,
copy the file `default-config.yaml` to `custom-config.yaml`,
and you can change the parent source directory and the names and commands
of each project.

Note that if the source directory is changed the virtual machines must be
reloaded, to mount the proper directory.

Take a look to the `install` script to see the advanced options.


## Running the Tests

Once all the machines are up and provisioned, and Clara is installed,
run all the tests with:

    $ ./run

The result of the tests will be printed in the standard output.
The Clara logs can be found in `$CLARA_HOME/log`.


## Manual Testing and Development

All the scripts are designed to run inside the virtual machines (the
`install` and `run` scripts are simple ssh wrappers).

It is recommended to use the _platform_ node to manually run and check Clara
commands (or the scripts).

    $ vagrant ssh platform

In the _platform_, an scripted **tmux** development session is ready to be
launched:

    $ clara-testing
