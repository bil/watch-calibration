# watch-calibration

This simple watch calibration experiment showcases how an experiment workflow might be designed to be compatible with the ARTS open framework. It includes raw audio data of a watch movement ticking and is written as a Python package with accompanying helper scripts that can be run in a container.

The following ARTS open framework features are implemented:

- config.env file
- open-source license
- usage documentation for experiment workflow
- persistent storage in compatible archive
- code tracking ia trusted-timestamped git repository
- data tracking via manual trusted timestamping
- containerized environment exposing figure generation code, development environment, interactive plots, and data collection pipeline
- container image

This comprehensive set of features may be pared down to fit the needs of the research output. For example, a dataset being released under the ARTS open framework might exclude analysis code, a git repository, and scripts unrelated to data collection.

The experiment is most easily followed using the included jupyter notebook which may be run with or without a container.

## Container Usage

All container functionality is made available using the `./run.sh` script. The default functionality is to generate plots and other functionality is made available through passing command line arguments.

### Setup

Make sure you have an OCI-compatible container engine installed. This example has been tested with both Podman (5.1.1) and Docker (4.37.2).

Installation instructions for both engines can be found here:

- [Podman](https://podman.io/docs/installation)
- [Docker](https://docs.docker.com/engine/install/).

### Configuration

Modify config.env as needed. The default values allow you to reproduce the experiment as initially run, but if you'd like to try the experiment on your own data, you can specify a different path for `ARTS_RAW_DATA_PATH` or move your data to the path specified and update the code instead.

### Generate Figures

Figures relating to the watch-calibration experiemnt included in the ARTS open framework paper can be recreated.

The following three commands are equivalent:


```bash
./run.sh
./run.sh g
./run.sh generate_figures
```

### Jupyter Notebook

To run jupyter notebook in the container and open up a jupyter notebook on your local port 8888, run:

```bash
./run.sh j
```

Then navigate to http://localhost:8888 in your browser. If you are running the paackage on a remote machine over SSH and would like to view the notebook on your local browser, you will need to run the SSH command using tunneling as follows:

```bash
ssh <remote> -L 8888:localhost:8888
```

To stop the server, the following can be run in another terminal:

```bash
ENGINE=podman
$ENGINE stop watch-calibration-jupyter
```

### IPython Kernel

To run an ipython kernel in the container, run:

```bash
./run.sh i
```

Once the ipython prompt shows up, data can be loaded and analysis run with:

```bash
wc = WatchCalibration()
wc.load_audio("raw_data/data_W241130_W241130.wav")
wc.generate_figures()
... TODO perform analysis command
```


### Container Image

To save the container image as a tar achive, the run script can be run with the save-image argument:

```bash
./run.sh s
```

Once an image is saved as watch-calibration.tar, that container image may be used to run containers instead of building locally. Just include the name of the container image as the second argument to the run script. For example, to generate plots using the saved image:

```bash
./run.sh g watch-calibration.tar
```


## Local Usage (without a container)

The experiment may also be run outside of a container for those wishing to build the environment from scratch or run the analysis with updated dependencies.


### Initial Setup

A setup script is provided that installs a Python virtual environment and all of the Python dependencies into that environment. This setup script uses pyenv in order to make the dependency management process more transparent, but another Python environment manager such as conda can easily be used by installing packages as specified in the incldued `requirements.txt` file.

```bash
./setup.sh
```

### Update Dependencies

Using pip-tools (pip-compile + pip-sync), new dependencies can be added to the experiment and versioned by updating the `requirements.in` file and running:

```bash
./update-deps.sh
```

This will automatically update the `requirements.txt` file with any new required dependencies including their versions.

## Rebuilding the container

The container build process was tested on a Nov 23 16-inch M3 Macbook Pro running macOS 14.5. Podman builds were tested using a machine with a maximum of 7 CPUs and 4GiB memory and Docker builds were tested with limits of 8 CPUs and 10 GB. The selection of these specs is arbitrary and do not represent requirements to build the container image.

To build the container on your machine using podman and save it to file, use the following:

```bash
podman machine init --cpus 7 -m 4096
podman machine start
./run.sh -s
```
