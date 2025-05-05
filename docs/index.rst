PyRMQ
=====
.. image:: https://img.shields.io/github/workflow/status/first-digital-finance/pyrmq/Test%20across%20Python%20versions?style=for-the-badge
    :target: https://github.com/first-digital-finance/pyrmq

.. image:: https://img.shields.io/pypi/v/pyrmq?style=for-the-badge
    :target: https://pypi.org/project/PyRMQ/

.. image:: https://app.readthedocs.org/projects/pyrmq/badge/?version=latest&style=for-the-badge
    :target: https://pyrmq.readthedocs.io/en/latest/

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
- Works with Python 3.11-3.13.
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
PyRMQ supports two ways to prioritize messages:

1. **Quorum queues (recommended)**: Use the `is_priority` flag to set a priority of 5 (high priority).

   .. code-block:: python

       from pyrmq import Publisher
       publisher = Publisher(
           exchange_name="exchange_name",
           queue_name="queue_name",
           routing_key="routing_key",
       )
       publisher.publish({"pyrmq": "High priority message"}, is_priority=True)  # Priority 5
       publisher.publish({"pyrmq": "Normal message"})  # Default priority 0
   
   In quorum queues, messages with priority 5-255 are considered high priority, and those with priority 0-4 are normal priority. When both types exist in the queue, RabbitMQ maintains a 2:1 ratio, delivering at least 2 high priority messages for every 1 normal priority message.

2. **Classic queues**: For finer-grained control with numeric priorities, configure your Consumer with the `x-max-priority` 
   argument and use message properties when publishing.

   .. code-block:: python

       # When setting up the Consumer
       consumer = Consumer(
           exchange_name="exchange_name",
           queue_name="queue_name",
           routing_key="routing_key",
           queue_args={"x-queue-type": "classic", "x-max-priority": 5},
           callback=callback
       )
       
       # When publishing
       publisher.publish({"pyrmq": "Priority message"}, message_properties={"priority": 3})

Read more about message priorities `here`_

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
in queues while retrying periodically for a set amount of times.

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

DLX-DLK Retry backoff vs Periodic retries
-----------------------------------------
Since `RabbitMQ does not remove expired messages that aren't at the head of the queue`_,
this leads to a congestion of the retry queue that is bottlenecked with an unexpired message
at the head. As such, as of 3.3.0, PyRMQ will be using a simple periodic retry.

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


Binding an exchange to another exchange
_______________________________________
By default, the ``exchange_name`` you pass when initializing a ``Consumer`` is declared and bound to the passed
``queue_name``. What if you want to bind and declare this exchange to another exchange as well?

This is done by using ``bound_exchange``. This parameter accepts an object with two keys: ``name`` of your exchange
and its ``type``. Let's take a look at an example to see this in action.

.. code-block:: python

    from pyrmq import Consumer

    def callback(data):
        print(f"Received {data}!")
        raise Exception

    consumer = Consumer(
        exchange_name="direct_exchange",
        queue_name="direct_queue",
        routing_key="routing_key",
        bound_exchange={"name": "headers_exchange_name", "type": "headers"},
        callback=callback,
        is_dlk_retry_enabled=True,
    )
    consumer.start()

In the example above, we want to consume from an exchange called ``direct_exchange`` that is directly bound to queue
``direct_queue``. We want `direct_exchange` to get its messages from another exchange called ``headers_exchange_name``
of type ``headers``. By using ``bound_exchange``, PyRMQ declares ``direct_exchange`` and ``direct_queue`` along with
any queue or exchange arguments you may have first then declares the bound exchange next and binds them together. This
is done to alleviate the need to declare your bound exchange manually.

.. warning::

    Since this method uses `e2e bindings`_, if you're using a headers exchange to bind
    your consumer to, they _and_ your publisher must all have the same routing key to route the messages properly. This
    is not needed for exchange to queue bindings as the routing key is optional for those.

User Guide
----------
.. toctree::
    Installation <install>
    Usage <usage>
    API <api>
    Testing <testing>

.. _pika: https://pypi.org/project/pika/
.. _default initialization settings: https://hub.docker.com/_/rabbitmq
.. _PyPI: https://pypi.org/project/PyRMQ/
.. _here: https://www.rabbitmq.com/docs/priority
.. _dead letter exchanges and queues: https://www.rabbitmq.com/docs/dlx
.. _RabbitMQ does not remove expired messages that aren't at the head of the queue: https://www.rabbitmq.com/docs/ttl
.. _e2e bindings: https://www.rabbitmq.com/docs/e2e
