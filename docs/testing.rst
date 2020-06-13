Testing PyRMQ
================

We're not gonna lie. Testing RabbitMQ, mocks or not, is infuriating. Much harder than a traditional
integration testing with a database. That said, we hope that you could help us expand on
what we have started should you feel our current tests aren't enough.

RabbitMQ
--------
Since PyRMQ strives to be as complete with testing as it can be, it has several integration tests
that need a running RabbitMQ to pass. Currently, PyRMQ is tested against ``rabbitmq:3.8``.

Run Docker image (recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code-block:: console

    $ docker run -d --hostname my-rabbit --name rabbitmq -p 5672:5672 rabbitmq:alpine

This allows you to connect to RabbitMQ via http://127.0.0.1:5672. Default credentials are
``guest``/``guest``.

Install and run RabbitMQ locally
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

    $ # Depending on your OS
    $ # Ubuntu
    $ sudo apt install rabbitmq
    $ # Arch Linux
    $ sudo pacman -S rabbitmq

Using tox
---------
Install ``pip install tox`` and run:

.. code-block:: console

    $ tox
    $ tox -e py38  # If this is what you have installed or don't want to bother testing for other versions

