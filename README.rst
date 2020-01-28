prepull-singularity
===================
Application to populate the singularity cache. Useful for HPC clusters where
multiple nodes may pull to the same cache at the same time if images are not
yet present.

Installation
-------------
prepull-singularity is tested on python 3.5, 3.6, 3.7 and 3.8. It can be
installed with:

``pip install prepull-singularity``

How to run
----------

1. Make a YAML file listing the images to be pulled.

.. code-block:: yaml

    alpine: "alpine:latest"
    debian: "debian:stretch-slim"

2. Run the program ``prepull-singularity images.yml``

Usage
-----

.. code-block:: text

    usage: prepull-singularity [-h] [-a MAX_ATTEMPTS] [-p PREFIX]
                               [--stop-on-failure] [--show-output-on-failure]
                               [--show-output-on-success]
                               [--singularity-exe SINGULARITY_EXE] [--use-digest]
                               input

    Pull images from listed in a YAML file, so they get cached and can be run
    without pulling later.

    positional arguments:
      input                 A YAML file listing the images to be pulled, either as
                            a map or list.

    optional arguments:
      -h, --help            show this help message and exit
      -a MAX_ATTEMPTS, --max-attempts MAX_ATTEMPTS
                            Maximum number of times to attempt pulling each image;
                            defaults to 3.
      -p PREFIX, --prefix PREFIX
                            Prefix for the image url; defaults to 'docker://'.
      --stop-on-failure     Stop when pulling an image fails; by default all
                            images will be attempted to be pull even if one fails.
      --show-output-on-failure
                            Print the stderr and stdout when pulling an image
                            fails.
      --show-output-on-success
                            Print the stderr and stdout when pulling an image
                            succeeds.
      --singularity-exe SINGULARITY_EXE
                            The command for running singularity; defaults to
                            'singularity'
      --use-digest          Retrieve the image digestes from dockerhub or quay.io
                            and use those (instead of the tags) to pull the
                            images. Only usable with docker images.
