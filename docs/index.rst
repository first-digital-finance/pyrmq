PyRMQ
=====
.. image:: https://img.shields.io/github/workflow/status/first-digital-finance/pyrmq/Test%20across%20Python%20versions?style=for-the-badge
    :target: https://github.com/first-digital-finance/pyrmq

.. image:: https://img.shields.io/pypi/v/pyrmq?style=for-the-badge
    :target: https://pypi.org/project/PyRMQ/

.. image:: https://readthedocs.org/projects/pyrmq/badge/?version=latest&style=for-the-badge
    :target: https://pyrmq.readthedocs.io

.. image:: https://img.shields.io/pypi/pyversions/pyrmq?style=for-the-badge
    :target: https://pypi.org/project/PyRMQ/

.. image:: https://img.shields.io/badge/license-MIT-blue.svg?longCache=true&style=for-the-badge
    :target: https://altusgerona.mit-license.org

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg?longCache=true&style=for-the-badge
    :target: https://github.com/psf/black

.. image:: https://img.shields.io/badge/%20imports-isort-%231674b1?style=for-the-badge&labelColor=ef8336)](https://pycqa.github.io/isort/
    :target: https://github.com/PyCQA/isort

Python with RabbitMQ—simplified so you won't have to.

Features
--------
Stop worrying about boilerplating and implementing retry logic on your queues. PyRMQ already
does it for you.

- Use out-of-the-box :class:`~pyrmq.Consumer` and :class:`~pyrmq.Publisher` classes created from `pika`_ for your projects and tests.
- Custom DLX-DLK-based retry logic for message consumption.
- Message priorities
- Works with Python 3.
- Production ready

Quickstart
----------
PyRMQ is available at `PyPI`_.

.. code-block:: console

    $ pip install pyrmq

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

Publish message with priorities
-------------------------------
To enable prioritization of messages, instantiate your queue with the queue
argument `x-max-priority`. It takes an integer that sets the number of possible
priority values with a higher number commanding more priority. Then, simply
publish your message with the priority argument specified. Any number higher
than the set max priority is floored or considered the same.
Read more about message priorities `here`_

.. code-block:: python

    from pyrmq import Publisher
    publisher = Publisher(
        exchange_name="exchange_name",
        queue_name="queue_name",
        routing_key="routing_key",
        queue_args={"x-max-priority": 3}
    )
    publisher.publish({"pyrmq": "My first message"}, priority=1)

.. warning::

    Adding arguments on an existing queue is not possible. If you wish to add queue arguments,
    you will need to either delete the existing queue then recreate the queue with arguments or simply
    make a new queue with the arguments.

Consuming
----------
Instantiating a :class:`~pyrmq.Consumer` automatically starts it in its own thread making it
non-blocking by default. When run after the code from before, you should be
able to receive the published data.

.. code-block:: python

    from pyrmq import Consumer


    def callback(data):
        print(f"Received {data}!")

    consumer = Consumer(
        exchange_name="exchange_name",
        queue_name="queue_name",
        routing_key="routing_key",
    )

    consumer.start()


DLX-DLK Retry Logic
-------------------
What if you wanted to retry a failure on a consumed message? PyRMQ offers a custom solution that keeps your message
in queues while retrying in an `exponential backoff`_ fashion.

This approach uses `dead letter exchanges and queues`_ to republish a message to your
original queue once it has expired. PyRMQ creates this "retry" queue for you with the default naming convention of
appending your original queue with `.retry`.

.. code-block:: python

    from pyrmq import Consumer

    def callback(data):
        print(f"Received {data}!")
        raise Exception

    consumer = Consumer(
        exchange_name="exchange_name",
        queue_name="queue_name",
        routing_key="routing_key",
        callback=callback,
        is_dlk_retry_enabled=True,
    )
    consumer.start()

This will start a loop of passing your message between the original queue and the retry queue until it reaches
the default number of ``max_retries``.


Using other exchange types
--------------------------
You can use another exchange type just by simply specifying it in the Publisher class. The default is
``direct``.

.. code-block:: python
    from pyrmq import Publisher

    queue_args = {"routing.sample": "sample", "x-match": "all"}

    publisher = Publisher(
        exchange_name="exchange_name",
        exchange_type="headers",
        queue_args=queue_args
    )

    message_properties = {"headers": {"routing.sample": "sample"}}
    publisher.publish({"pyrmq": "My first message"}, message_properties=message_properties)


This is an example of how to publish to a headers exchange that will get routed
based on its headers.

User Guide
----------
.. toctree::
    Installation <install>
    Usage <usage>
    API <api>
    Testing <testing>

.. _pika: https://pypi.org/project/pika/
.. _default initialization settings: https://hub.docker.com/_/rabbitmq)
.. _PyPI: https://pypi.org/project/PyRMQ/
.. _here: https://www.rabbitmq.com/priority.html
.. _exponential backoff: https://en.wikipedia.org/wiki/Exponential_backoff
.. _dead letter exchanges and queues: https://www.rabbitmq.com/dlx.html
