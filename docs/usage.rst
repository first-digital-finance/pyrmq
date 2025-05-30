How to use PyRMQ
================

Publishing
----------
Instantiate the :class:`~pyrmq.Publisher` class and plug in your application
specific settings. PyRMQ already works out of the box with RabbitMQ's `default initialization settings`_.

.. note::
   The Publisher class only verifies that exchanges exist and does not create queues or exchanges.
   Exchanges must be created by a Consumer before a Publisher can use them.

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
PyRMQ supports message priorities for both quorum and classic queues.

For quorum queues (the default), simply use the ``is_priority`` flag:

.. code-block:: python

    from pyrmq import Publisher
    publisher = Publisher(
        exchange_name="exchange_name",
        queue_name="queue_name",
        routing_key="routing_key",
    )
    publisher.publish({"pyrmq": "High priority message"}, is_priority=True)  # Priority 5
    publisher.publish({"pyrmq": "Normal message"})  # Default priority 0

In quorum queues, messages with priority 5-255 are considered high priority, while messages
with priority 0-4 are normal priority. When both high and normal priority messages exist
in the queue, RabbitMQ will deliver at least 2 high priority messages for every 1 normal
priority message, following a 2:1 ratio.

For classic queues with finer-grained priority control, you can still use the classic
priority system by configuring a queue with the ``x-max-priority`` argument and manually
specifying a numeric priority value.

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

DLX-DLK Consumption Retry Logic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PyRMQ calls pika's `start_consuming`_ when :class:`~pyrmq.Consumer` is instantiated. If your consumption callback
throws an exception, PyRMQ uses `dead letter exchanges and queues`_ to republish your messages to your
original queue once it has expired. PyRMQ already creates this "retry" queue for you with the default naming convention
of appending your original queue with `.retry`. This is simply enabled by setting the ``is_dlk_retry_enabled`` flag
on the :class:`~pyrmq.Consumer` class to ``True``.

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

Max retries reached
~~~~~~~~~~~~~~~~~~~
When PyRMQ has tried one too many times, it will call your specified callback.

.. _default initialization settings: https://hub.docker.com/_/rabbitmq
.. _BlockingConnection: https://pika.readthedocs.io/en/stable/modules/adapters/blocking.html
.. _basic_publish: https://pika.readthedocs.io/en/stable/modules/channel.html#pika.channel.Channel.basic_publish
.. _start_consuming: https://pika.readthedocs.io/en/stable/modules/adapters/blocking.html#pika.adapters.blocking_connection.BlockingChannel.start_consuming
.. _basic_ack: https://pika.readthedocs.io/en/stable/modules/channel.html#pika.channel.Channel.basic_ack
.. _here: https://www.rabbitmq.com/docs/priority
.. _dead letter exchanges and queues: https://www.rabbitmq.com/docs/dlx
