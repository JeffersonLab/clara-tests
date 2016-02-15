CLARA Stress Tests
==================

These scripts use tmux to launch the CLARA front-end and the specified number
of DPEs. When the tmux session is terminated, all CLARA processes will be
automatically killed.


Configuration
-------------

 -  Create a `services.yaml` file describing your reconstruction chain.
    Each service should be specified with the following format:

        - class: <service_class_name>
          name: <service_name>
          container: <container_name>

    The container setting is optional. If a global container value is set in
    the file, it will be used for all services that do not have a container
    field in its specification. The default container name is `USERNAME`.

    Use the distributed `services.yaml.sample` file as a template.
    Note that indentation is important.

    Services will be linked in the order they appear in the file.

Usage
-----

 -  Execute the `start` script to launch the front-end and the DPEs:

        $ ./start <number_of_dpes>

    A tmux session will be created. Window 1 will show the front-end running
    and each of the next windows will show the running DPEs. The focus will be
    in Window 0, to run the following scripts.

    If the number of DPEs is set to 0 then no DPE will be started, and only
    the front-end will be used to run services.

 -  Execute the `setup-chain` script with the services.yaml file as argument
    to deploy and link the reconstruction services.

        $ ./setup-chain <services.yaml>

    The standard reader and writer will be deployed in the front-end.
    The reconstruction chain will be deployed on each running DPE. If no DPEs
    were started, then the chain will be deployed in the front-end.

    Once all the services in all nodes are deployed, the reader will be linked
    to the first service of the reconstruction chain in each DPE. The last
    service of the chains will be linked to the writer, and finally the writer
    will be linked back to the reader.


                 --> N1:S1 ---> N1:S2 ---> N1:S3 --
                /                                  \
        --> R -----> N2:S1 ---> N2:S2 ---> N2:S3 -----> W --
        |       \                                  /       |
        |        --> N3:S1 ---> N3:S2 ---> N3:S3 --        |
        |                                                  |
        \                                                 /
         ------------------------<------------------------

    Thus, the reader will not start a new event until a previous one was
    reconstructed.

 -  Execute the `run` script to launch the reconstruction.

        $ ./run <input_file> <output_file> <number_of_cores>

    This script will launch the `DefaultOrchestrator`, provided by CLARA.
    It will configure the reader to read events from the given <input_file>
    and the writer to save the reconstructed events to <output_file>.

    The <number_of_cores> parameter specifies how many parallel threads should
    be used on each node to run the reconstruction chain, i.e., how many
    events will be reconstructed in parallel on each node.

    The orchestrator will print the average processing time of the
    reconstructed events. It is updated each 1000 events, i.e, the third
    message will print the average time of the 3000 reconstructed events so
    far, etc.

 -  Once the reconstruction is done, execute the `quit` script to terminate the
    tmux session, kill all CLARA processes and remove temporary files.

        $ ./quit

    Alternatively, CLARA processes can be killed one by one by moving to each
    window in the tmux session and hitting `C-c`.

    Don't keep CLARA running after finishing the reconstruction.
