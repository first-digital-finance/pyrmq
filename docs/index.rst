PyRMQ
=====
.. image:: https://img.shields.io/badge/license-MIT-blue.svg?longCache=true&style=for-the-badge
    :target: https://altusgerona.mit-license.org

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg?longCache=true&style=for-the-badge
    :target: https://github.com/psf/black

Python with RabbitMQ—simplified so you won't have to.

Features
--------
Stop worrying about boilerplating and implementing retry logic on your queues. PyRMQ already
does it for you.

- Use out-of-the-box and thread-safe `Consumer` and `Publisher` classes created from `pika`_ for your projects and tests.
- Built-in retry-backoff logic for connecting, consuming, and publishing.
- Works with Python 3.
- Production ready.

Quickstart
----------
Just instantiate the feature you want with their respective settings.
PyRMQ already works out of the box with RabbitMQ's `default initialization settings`_.

.. code-block:: python

    from pyrmq import Publisher
    publisher = Publisher(
        exchange_name="exchange_name",
        queue_name="queue_name",
        routing_key="routing_key",
    )
    publisher.publish({"pyrmq": "My first message"})

User Guide
----------
.. toctree::
    Installation <install>
    Usage <usage>
    API <api>
    Testing <testing>

.. _pika: https://pypi.org/project/pika/
.. _default initialization settings: https://hub.docker.com/_/rabbitmq)
