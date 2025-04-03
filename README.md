# watch-calibration

This watch calibration example showcases how an experiment might be designed to be compatible with the ARTS open framework. It includes raw audio data of a watch movement ticking and is written as a Python package. The experiment is most easily followed using the included jupyter notebook.

The experiment may be run with or without a container.

## Container Usage

All container functionality is made available using the `./run.sh` script. The default functionality is to generate plots and other functionality is made available through passing command line arguments.

### Configuration

Modify config.env

### Generate Figures

```bash
./run.sh
```

```bash
./run.sh -g
```

### Jupyter Notebook

To run jupyter notebook in the container and open up a jupyter notebook on your local port 8888, run:

```bash
./run.sh -j
```

Then navigate to the link starting with http://localhost:8888/tree?token=<token> displayed in your terminal.

To stop the server, the following can be run in another terminal:

```bash
ENGINE=podman
$ENGINE stop watch-calibration-jupyter
```

### IPython Kernel

And to run an ipython kernel in the container, run:

```bash
./run.sh -i
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
./run.sh -s
```

And to load the image back, run:

```bash
./run.sh -l
```


## Local Usage (without a container)

The experiment may also be run outside of a container for those wishing to build the environment from scratch or run the analysis with updated dependencies.

### Initial Setup

```bash
./setup.sh
```

### Update Dependencies

Add new dependencies to `requirements.in` and then run:

```bash
./update-deps.sh
```

## Rebuilding the container

podman 7cpus, 4GiB memory


## Publish Package

Get S3-like credentials from: https://archive.org/account/s3.php

TODO
