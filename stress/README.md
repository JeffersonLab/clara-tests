# CLARA Stress Tests

These scripts use tmux to launch the CLARA front-end
and a specified number of DPEs.
When the tmux session is terminated,
all CLARA processes will be automatically killed.


## Setup

Create a `services.yaml` file describing your reconstruction chain.
Each service should be specified with the following format:

    - class: <service_class_name>
      name: <service_name>

The default container name is `USERNAME`.

Use the distributed `services.yaml.sample` file as a template.
Note that indentation is important.

Services will be linked in the order they appear in the file.

## Start

Execute the `start` script to launch the local front-end DPE:

    $ ./start <number_of_dpes>

A tmux session will be created. Pane 1 will show the front-end running and
each of the next panes will show the running DPEs.
The focus will be in last pane, to run the reconstruction/stress scripts.

If the number of DPEs is set to 0 then no DPE will be started,
and only the front-end will be used to run services.


## Scripts

### `run-local`

The `run-local` script can be used to reconstruct a file on the local box:

    $ ./run-local [ -t <num_cores> ] <services_file> <input_file> <output_file>

All services will be deployed on the local front-end DPE.
The reader will be configured to read events from the given `<input_file>`
and the writer to save the reconstructed events to `<output_file>`.

The `<num_cores>` parameter specifies how many parallel threads
should be used to run the reconstruction chain, i.e.,
how many events will be reconstructed in parallel.

The orchestrator will print the average processing time of the
reconstructed events. It is updated each 1000 events, i.e,
the third message will print the average time of the 3000 reconstructed
events so far, etc.

### `run-cloud`

The `run-cloud` script can be used to reconstruct a list of files using
multiple DPE workers.

    $ ./run-cloud [ -i <input_dir> ] [ -o <output_dir> ] <services_file> <input_files>

Each DPE will be contain its own I/O services and reconstruction chain,
and it will be assigned to process the next file of the list. 

The `<input_dir>` and `<output_dir>` should point to the location of the files.
The files can optionally be staged into the local file system of each DPE.
See the help for a full list of options.

The orchestrator will print the average processing time once all files have
bee reconstructed.

### `multicore-test`

The `multicore-test` runs the local reconstruction multiple times,
looping the number of reconstruction threads from 1 to all available cores.

    $ ./multicore-test <services_file> <input_file> <output_file>

For each number of threads, the reconstruction will run three times.
The average reconstruction times are stored in CSV format,
and they can be used to generate a scaling plot.
For long running stress test, a mail can be sent when the test has finished.
See the help for a full list of options.

## Exit

Once everything is done, execute the `quit` script to terminate the tmux
session, kill all CLARA processes and remove temporary files.

    $ ./quit

Alternatively, CLARA processes can be killed one by one by moving to each tmux
pane and hitting `C-c`.

Don't keep CLARA running after finishing the reconstruction.

