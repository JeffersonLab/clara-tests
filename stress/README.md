# CLARA Stress Tests

These scripts use tmux to launch the CLARA front-end
and a specified number of DPEs.
When the tmux session is terminated,
all CLARA processes will be automatically killed.


## Setup

Create a `services.yml` file describing the application to be tested.
Each service should be specified with the following key/value pairs:

    class: <service_class_name>
    name: <service_name>

The default container for all services is is `USERNAME`.

The `io-services` section must have the `reader` and `writer` keys
declaring the I/O services that will process the set of files.
The `services` section must contain the list of reconstruction services. 
The services will be linked in the order they appear in this list.
Finally, the `mime-types` section is also required in order to
list the data types used by the services.

    ---
    io-services:
      reader:
        class: org.jlab.clas.std.services.convertors.HipoToHipoReader
        name: HipoToHipoReader
      writer:
        class: org.jlab.clas.std.services.convertors.HipoToHipoWriter
        name: HipoToHipoWriter
    services:
      - class: org.jlab.service.dc.DCHBEngine
        name: DCHB
      - class: org.jlab.service.dc.DCTBEngine
        name: DCTB
      - class: org.jlab.service.ec.ECEngine
        name: EC
    mime-types:
      - binary/data-hipo

Use the distributed `services.yml.sample` file as a template.
Note that indentation is important.

## Start

Execute the `start` script to launch the local front-end DPE:

    $ ./start [ <number_of_dpes> ]

A tmux session will be created. Pane 1 will show the front-end running and
each of the next panes will show the running worker DPEs, if any.
The focus will be in last pane, to run the stress test scripts.

If the number of worker DPEs is not set,
then only the local front-end will be used to run services.


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
For long running stress test, a mail can be sent when the test has finished.
See the help for a full list of options.


## Results

### `multicore-test`

The `multicore-test` creates a `results.csv` file in the log directory with
the average reconstruction times, that can be used to generate a scaling plot.
It also saves the full log of all orchestrator runs in the `run.log` file.

To get execution times for all services, and generate a Jupyter notebook,
the `run.log` file can be parsed using the Python scripts
distributed in the `ana` directory.

1. Create a Python virtual environment and install the required packages:

        $ pip install -r requirements.txt

2. Get execution times for all services in CSV format:

        $ ./ana/multicore-results <run.log>

3. (Optionally) Use a [Jupyter notebook][jupyter_nb] to analyse data:

    1.  Generate a notebook with the entire data and scaling plots:

            $ ./ana/multicore-results --nb-file <notebook.ipynb> <run.log>

    2.  Start the Jupyter Notebook App:
    
            $ jupyter notebook

    3.  Open the generated notebook file and [run all cells][exec_nb]
        from the menu _Cell -> Run All_.

    An example notebook (without input cells) can be found [here][sample_nb].

[jupyter_nb]: https://jupyter-notebook.readthedocs.io/en/stable/
[exec_nb]: http://jupyter-notebook-beginner-guide.readthedocs.io/en/latest/execute.html
[sample_nb]: https://claraweb.jlab.org/results/scaling/coat/clara-scaling-coat-5a.1.3-20180314.html


## Exit

Once everything is done, execute the `quit` script to terminate the tmux
session, kill all CLARA processes and remove temporary files.

    $ ./quit

Alternatively, CLARA processes can be killed one by one by moving to each tmux
pane and hitting `C-c`.

Don't keep CLARA running after finishing the reconstruction.

