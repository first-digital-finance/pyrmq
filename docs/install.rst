PyRMQ Installation
==================

There are multiple ways to install PyRMQ as long as multiple versions to
choose from.


Stable Version
--------------

PyRMQ is available at `PyPI`_.

.. code-block:: console

    $ pip install pyrmq


Development Version
-------------------

Since PyRMQ is continuously used in a growing number of internal microservices
all working with RabbitMQ, you can see or participate in its active
development in its `GitHub repository`_.

Development with UV
~~~~~~~~~~~~~~~~~~

This project uses `UV <https://github.com/astral-sh/uv>`_, a fast Python package installer and resolver written in Rust.

.. code-block:: console

    # Install UV
    $ curl -LsSf https://astral.sh/uv/install.sh | sh

    # Clone the repository
    $ git clone git@github.com:first-digital-finance/pyrmq.git
    $ cd pyrmq

    # Create a virtual environment
    $ uv venv

    # Activate the virtual environment
    $ source .venv/bin/activate  # Linux/macOS
    $ .venv\Scripts\activate     # Windows

    # Install the package with development dependencies
    $ uv add -e .[dev]

This will setup PyRMQ and its dependencies on your local machine.
Just fetch/pull code from the master branch to keep your copy up to date.

Install from GitHub
~~~~~~~~~~~~~~~~~~

.. code-block:: console

    $ mkdir pyrmq
    $ cd pyrmq
    $ python -m venv venv
    $ . venv/bin/activate
    $ pip install git+https://github.com/first-digital-finance/pyrmq.git


.. _GitHub repository: https://github.com/first-digital-finance/pyrmq
.. _PyPI: https://pypi.org/project/PyRMQ/
