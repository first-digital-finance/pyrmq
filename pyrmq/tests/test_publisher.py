"""
    Python with RabbitMQ—simplified so you won't have to.

    :copyright: 2020-Present by Alexandre Gerona.
    :license: MIT, see LICENSE for more details.

    Full documentation is available at https://pyrmq.readthedocs.io
"""

from typing import Dict
from unittest.mock import PropertyMock, patch

import pytest
from pika.exceptions import (
    AMQPChannelError,
    AMQPConnectionError,
    ChannelClosedByBroker,
    UnroutableError,
)

from pyrmq import Consumer, Publisher
from pyrmq.publisher import CONNECT_ERROR
from pyrmq.tests.conftest import TEST_EXCHANGE_NAME, TEST_QUEUE_NAME, TEST_ROUTING_KEY
from pyrmq.tests.test_consumer import assert_consumed_message


def should_handle_connection_error_when_connecting():
    from pyrmq import Publisher

    publisher = Publisher(
        exchange_name="incorrect_exchange_name",
        queue_name="incorrect_queue_name",
        routing_key="incorrect_routing_key",
        username="incorrect_username",  # BlockingConnection class from pika goes on an infinite loop if credentials are wrong.
    )

    with patch(
        "pika.adapters.blocking_connection.BlockingConnection.__init__",
        side_effect=AMQPConnectionError,
    ):
        with patch("time.sleep") as sleep:
            # noinspection PyTypeChecker
            with pytest.raises(
                (
                    TypeError,
                    AMQPConnectionError,
                )
            ):
                publisher.publish({})

    assert sleep.call_count == 2


def should_handle_connection_error_when_publishing():
    def error_callback(*args, **kwargs):
        assert kwargs["error_type"] == CONNECT_ERROR

    # Create a consumer first to declare the exchange so verify_exchange doesn't fail
    from pyrmq import Consumer

    dummy_consumer = Consumer(
        exchange_name="incorrect_exchange_name",
        queue_name="incorrect_queue_name",
        routing_key="incorrect_routing_key",
        callback=lambda x: x,
    )
    # Connect and declare the exchange
    dummy_consumer.connect()
    dummy_consumer.declare_queue()

    publisher = Publisher(
        exchange_name="incorrect_exchange_name",
        queue_name="incorrect_queue_name",
        routing_key="incorrect_routing_key",
        error_callback=error_callback,
    )
    body = {"sample_body": "value"}

    with patch(
        "pika.adapters.blocking_connection.BlockingChannel.basic_publish",
        side_effect=AMQPConnectionError,
    ):
        with patch("time.sleep") as sleep:
            with pytest.raises(AMQPConnectionError):
                publisher.publish(body)

    assert sleep.call_count == publisher.connection_attempts - 1


def should_handle_channel_error_when_publishing(publisher_session):
    body = {"sample_body": "value"}

    with patch(
        "pika.adapters.blocking_connection.BlockingChannel.basic_publish",
        side_effect=AMQPChannelError,
    ):
        with patch("time.sleep") as sleep:
            with pytest.raises(AMQPChannelError):
                publisher_session.publish(body)

    assert sleep.call_count == publisher_session.connection_attempts - 1


def should_handle_exception_from_error_callback():
    def error_callback(*args, **kwargs):
        raise Exception

    publisher = Publisher(
        exchange_name="incorrect_exchange_name",
        queue_name="incorrect_queue_name",
        routing_key="incorrect_routing_key",
        error_callback=error_callback,
    )
    body = {"sample_body": "value"}

    with patch(
        "pika.adapters.blocking_connection.BlockingChannel.basic_publish",
        side_effect=AMQPConnectionError,
    ):
        with patch("time.sleep") as sleep:
            with pytest.raises(AMQPConnectionError):
                publisher.publish(body)

    assert sleep.call_count == publisher.connection_attempts - 1


def should_throw_error_on_non_existing_exchange():
    """Test that an exception is raised when trying to publish to a non-existing exchange."""
    publisher = Publisher(
        exchange_name="non_existing_exchange",
        queue_name="non_existing_queue",
        routing_key="non_existing_routing_key",
    )

    with pytest.raises(ChannelClosedByBroker):
        publisher.publish({})


def should_handle_infinite_retry():
    publisher = Publisher(
        exchange_name="incorrect_exchange_name",
        queue_name="incorrect_queue_name",
        routing_key="incorrect_routing_key",
        infinite_retry=True,
    )

    with patch(
        "pika.adapters.blocking_connection.BlockingConnection.__init__",
        side_effect=AMQPConnectionError,
    ):
        with patch("time.sleep", side_effect=[None, None, Exception]) as sleep_call:
            # noinspection PyTypeChecker
            with pytest.raises(Exception):
                publisher.publish({})

            assert sleep_call.call_count == 3


def should_handle_different_ident():
    with patch("threading.Thread.ident", new_callable=PropertyMock) as mock_ident:
        mock_ident.side_effect = [11111, 22222]

        with patch("pika.adapters.blocking_connection.BlockingChannel.basic_publish"):
            publisher = Publisher(
                exchange_name=TEST_EXCHANGE_NAME,
                queue_name=TEST_QUEUE_NAME,
                routing_key=TEST_ROUTING_KEY,
            )
            publisher.publish({})
            publisher.publish({})


def should_publish_with_classic_queue():
    """Test that publishing works correctly using a classic queue"""
    classic_queue_name = "classic_publisher_test_queue"

    # Create a consumer first to declare the queue
    def callback(data, **kwargs):
        pass  # pragma: no cover

    consumer = Consumer(
        exchange_name=TEST_EXCHANGE_NAME,
        queue_name=classic_queue_name,
        routing_key=TEST_ROUTING_KEY,
        callback=callback,
        queue_args={"x-queue-type": "classic"},
    )

    # Make sure the queue exists
    consumer.connect()
    consumer.declare_queue()

    # Create a publisher with x-queue-type=classic
    publisher = Publisher(
        exchange_name=TEST_EXCHANGE_NAME,
        queue_name=classic_queue_name,
        routing_key=TEST_ROUTING_KEY,
        queue_args={"x-queue-type": "classic"},
    )

    # Publish a message
    test_message = {"test": "classic_publisher_test"}
    publisher.publish(test_message)

    # Verify the message was published by consuming it
    response = {}

    def callback(data, **kwargs):
        response.update(data)

    consumer = Consumer(
        exchange_name=TEST_EXCHANGE_NAME,
        queue_name=classic_queue_name,
        routing_key=TEST_ROUTING_KEY,
        callback=callback,
        queue_args={"x-queue-type": "classic"},
    )

    consumer.start()
    assert_consumed_message(response, test_message)
    consumer.close()

    # Clean up
    channel = publisher.connect()
    channel.queue_purge(classic_queue_name)
    channel.queue_delete(classic_queue_name)


def should_publish_to_the_routed_queue_as_specified_in_headers():
    """
    This creates two queues, `first_queue` and `second_queue`
    which are bound to one exchange of type `headers`. The
    first two publish methods are to create and bind the
    queues to the exchange. The third one is to simply
    test whether the first_queue gets the message just by
    setting the headers correctly.
    """

    exchange_headers_name = "test_headers_exchange"

    # First, create the consumers to declare the queues and exchanges
    def dummy_callback(data, **kwargs):
        pass  # pragma: no cover

    # Set up first queue and exchange
    first_queue_args = {"routing.first": "first", "x-match": "all"}
    first_consumer = Consumer(
        exchange_name=exchange_headers_name,
        queue_name="publisher_first_queue",
        routing_key="publisher_first_queue",
        queue_args=first_queue_args,
        exchange_type="headers",
        callback=dummy_callback,
    )
    first_consumer.connect()
    first_consumer.declare_queue()

    # Set up second queue and exchange
    second_queue_args = {"routing.second": "second", "x-match": "all"}
    second_consumer = Consumer(
        exchange_name=exchange_headers_name,
        queue_name="publisher_second_queue",
        routing_key="publisher_second_queue",
        queue_args=second_queue_args,
        exchange_type="headers",
        callback=dummy_callback,
    )
    second_consumer.connect()
    second_consumer.declare_queue()

    # Now create publishers and publish to queues

    # Create and publish to first queue with enabled routing.
    first_publisher = Publisher(
        exchange_name=exchange_headers_name,
        exchange_type="headers",
        queue_name="publisher_first_queue",
        routing_key="publisher_first_queue",
        queue_args=first_queue_args,
    )
    first_properties = {"headers": {"routing.first": "first"}}
    first_publisher.publish({"test": "test"}, message_properties=first_properties)

    # Create and publish to second queue with enabled routing.
    second_publisher = Publisher(
        exchange_name=exchange_headers_name,
        exchange_type="headers",
        queue_name="publisher_second_queue",
        routing_key="publisher_second_queue",
        queue_args=second_queue_args,
    )
    second_properties = {"headers": {"routing.second": "second"}}
    second_publisher.publish({"test": "test"}, message_properties=second_properties)

    # Publish to the first queue just by setting the routing in the headers.
    third_publisher = Publisher(
        exchange_name=exchange_headers_name,
        exchange_type="headers",
        queue_args=first_queue_args,
    )
    third_publisher.publish({"test": "test"}, message_properties=first_properties)

    first_response = {"count": 0}

    def first_callback(data: Dict, **kwargs):
        first_response["count"] += 1

    first_consumer = Consumer(
        exchange_name=exchange_headers_name,
        queue_name="publisher_first_queue",
        routing_key="publisher_first_queue",
        queue_args=first_queue_args,
        exchange_type="headers",
        callback=first_callback,
    )
    first_consumer.start()
    assert_consumed_message(first_response, {"count": 2})
    first_consumer.close()

    second_response = {"count": 0}

    def second_callback(data: Dict, **kwargs):
        second_response["count"] += 1

    second_consumer = Consumer(
        exchange_name=exchange_headers_name,
        queue_name="publisher_second_queue",
        routing_key="publisher_second_queue",
        queue_args=second_queue_args,
        exchange_type="headers",
        callback=second_callback,
    )
    second_consumer.start()
    assert_consumed_message(second_response, {"count": 1})
    second_consumer.close()


def should_raise_exception_if_exchange_exists_but_queue_does_not():
    """Test that publishing to an exchange with no matching queue raises UnroutableError."""
    # Create an exchange with no queue bound to it
    exchange_name = "isolated_exchange"

    # First, we need to declare the exchange through a consumer
    def dummy_callback(data, **kwargs):
        pass  # pragma: no cover

    # Create a consumer that just declares the exchange
    consumer = Consumer(
        exchange_name=exchange_name,
        queue_name="temp_queue",  # This queue won't be used
        routing_key="temp_key",
        callback=dummy_callback,
    )

    # Connect and declare the exchange, but we'll skip binding a queue to it
    consumer.connect()
    consumer.channel.exchange_declare(
        exchange=exchange_name, durable=True, exchange_type="direct"
    )

    # Create a publisher that will try to publish to the exchange
    publisher = Publisher(
        exchange_name=exchange_name,
        routing_key="non_existent_queue",  # No queue with this routing key exists
    )

    # Try to publish - should raise UnroutableError since no queue is bound to the exchange
    with pytest.raises(UnroutableError):
        publisher.publish({"test": "This message should be unroutable"})

    # Clean up
    channel = publisher.connect()
    channel.exchange_delete(exchange_name)
