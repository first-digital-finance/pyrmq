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

There are two ways to work or collaborate with its development version.

Git Checkout
~~~~~~~~~~~~
Clone the code from GitHub and run it in a `virtualenv`.

.. code-block:: console

    $ git clone git@github.com:first-digital-finance/pyrmq.git
    $ virtualenv venv --distribute
    $ . venv/bin/activate
    $ python setup.py install

This will setup PyRMQ and its dependencies on your local machine.
Just fetch/pull code from the master branch to keep your copy up to date.

PyPI
~~~~

.. code-block:: console

    $ mkdir pyrmq
    $ cd pyrmq
    $ virtualenv venv --distribute
    $ . venv/bin/activate
    $ pip install git+git://github.com/first-digital-finance/pyrmq.git


.. _GitHub repository: https://github.com/first-digital-finance/pyrmq
.. _PyPI: https://pypi.org/project/PyRMQ/
