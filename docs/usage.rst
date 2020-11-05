How to use PyRMQ
================

Publishing
----------
Instantiate the :class:`~pyrmq.Publisher` class and plug in your application
specific settings. PyRMQ already works out of the box with RabbitMQ's `default initialization settings`_.

.. code-block:: python

    from pyrmq import Publisher
    publisher = Publisher(
        exchange_name="exchange_name",
        queue_name="queue_name",
        routing_key="routing_key",
    )
    publisher.publish({"pyrmq": "My first message"})

This publishes a message that uses a `BlockingConnection`_ on its own thread with default settings and
and provides a handler for its retries.

Retries
~~~~~~~
PyRMQ's :class:`~pyrmq.Publisher` retries happen on two levels: connecting and publishing.

Connecting
~~~~~~~~~~
PyRMQ instantiates a `BlockingConnection`_ when connecting. If this fails, it will retry for
2 more times by default with a delay of 5 seconds, a backoff base of 2 seconds, and a backoff constant of 5 seconds.
All these settings are configurable via the :class:`~pyrmq.Publisher` class.

Publishing
~~~~~~~~~~
PyRMQ calls pika's `basic_publish`_ when publishing. If this fails, it will retry for
2 more times by default with a delay of 5 seconds, a backoff base of 2 seconds, and a backoff constant of 5 seconds.
All these settings are configurable via the :class:`~pyrmq.Publisher` class.

Max retries reached
~~~~~~~~~~~~~~~~~~~
When PyRMQ has tried one too many times, it will call your specified callback.

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
Instantiate the :class:`~pyrmq.Consumer` class and plug in your application specific settings.
PyRMQ already works out of the box with RabbitMQ's `default initialization settings`_.

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

Once the :class:`~pyrmq.Consumer` class is instantiated, just run ``start()`` to start its own thread that targets
pika's `start_consuming`_ method on its own thread with default settings and and provides a handler for
its retries. Consumption calls `basic_ack`_ with ``delivery_tag`` set to what the message's ``method``'s was.

Retries
~~~~~~~
PyRMQ's :class:`~pyrmq.Consumer` retries happen on two levels: connecting and consuming.

Connecting
~~~~~~~~~~
PyRMQ instantiates a `BlockingConnection`_ when connecting. If this fails, it will retry for
2 more times by default with a delay of 5 seconds, a backoff base of 2 seconds, and a backoff constant of 5 seconds.
All these settings are configurable via the :class:`~pyrmq.Consumer` class.

Consuming
~~~~~~~~~~
PyRMQ calls pika's `start_consuming`_ when :class:`~pyrmq.Consumer` is instantiated. If this fails, it will retry for
2 more times by default with a delay of 5 seconds, a backoff base of 2 seconds, and a backoff constant of 5 seconds.
All these settings are configurable via the :class:`~pyrmq.Consumer` class.

Max retries reached
~~~~~~~~~~~~~~~~~~~
When PyRMQ has tried one too many times, it will call your specified callback.

.. _default initialization settings: https://hub.docker.com/_/rabbitmq
.. _BlockingConnection: https://pika.readthedocs.io/en/stable/modules/adapters/blocking.html
.. _basic_publish: https://pika.readthedocs.io/en/stable/modules/channel.html#pika.channel.Channel.basic_publish
.. _start_consuming: https://pika.readthedocs.io/en/stable/modules/adapters/blocking.html#pika.adapters.blocking_connection.BlockingChannel.start_consuming
.. _basic_ack: https://pika.readthedocs.io/en/stable/modules/channel.html#pika.channel.Channel.basic_ack
.. _here: https://www.rabbitmq.com/priority.html