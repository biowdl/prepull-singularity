Prerequisites
-------------

* Python 3
  * PyYAML
* singularity
 

How to run
----------

1. Make a YAML file listing the images to be pulled.

.. code-block:: yaml

    alpine: "alpine:latest"
    debian: "debian:stretch-slim"

2. Run the script ``python prepull_singularity.py images.yml``
