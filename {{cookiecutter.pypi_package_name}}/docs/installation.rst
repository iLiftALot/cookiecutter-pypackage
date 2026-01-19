Installation
============

Requirements
------------

* Python {{ cookiecutter.python_version }} or higher

Install from source
-------------------

Clone the repository and install with pip:

.. code-block:: bash

   git clone https://github.com/{{cookiecutter.__gh_slug}}.git
   cd {{ cookiecutter.project_slug }}
   pip install -e .

Dependencies
------------

The following packages are installed automatically:

* ``pydantic`` - Data validation
* ``typer`` - CLI framework
* ``rich`` - Terminal formatting
* ``watchdog`` - File system monitoring
* ``pyyaml`` - YAML parsing
