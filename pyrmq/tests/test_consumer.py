"""
Python with RabbitMQ—simplified so you won't have to.

:copyright: 2020-Present by Alexandre Gerona.
:license: MIT, see LICENSE for more details.

Full documentation is available at https://pyrmq.readthedocs.io
"""

import logging
from random import randint
from time import sleep
from unittest.mock import Mock, patch

import pytest
from pika.exceptions import AMQPConnectionError

from pyrmq import Consumer, Publisher
from pyrmq.consumer import CONNECT_ERROR, CONSUME_ERROR
from pyrmq.tests.conftest import (
    TEST_EXCHANGE_NAME,
    TEST_PRIORITY_ARGUMENTS,
    TEST_QUEUE_NAME,
    TEST_ROUTING_KEY,
)


def assert_consumed_message(response, expected, tries=0, retry_after=0.6):
    if response == expected or tries > 5:
        assert response == expected
        return
    else:
        sleep(retry_after)
        return assert_consumed_message(response, expected, tries + 1)


def should_handle_exception_from_callback(publisher_session: Publisher):
    body = {"test": "test"}
    publisher_session.publish(body)

    response = {}

    def error_callback(*args, **kwargs):
        assert kwargs["error_type"] == CONSUME_ERROR

    def callback(data, **kwargs):
        response.update(data)
        raise Exception

    consumer = Consumer(
        exchange_name=publisher_session.exchange_name,
        queue_name=publisher_session.queue_name,
        routing_key=publisher_session.routing_key,
        callback=callback,
        error_callback=error_callback,
    )
    consumer.start()
    assert_consumed_message(response, body)
    consumer.close()


def should_handle_error_when_connecting(publisher_session):
    response = []

    def error_callback(*args, **kwargs):
        assert kwargs["error_type"] == CONNECT_ERROR
        response.append(1)

    with patch(
        "pika.adapters.blocking_connection.BlockingConnection.__init__",
        side_effect=AMQPConnectionError,
    ):
        with patch("time.sleep"):
            with pytest.raises(AMQPConnectionError):
                consumer = Consumer(
                    exchange_name=publisher_session.exchange_name,
                    queue_name=publisher_session.queue_name,
                    routing_key=publisher_session.routing_key,
                    callback=lambda x: x,
                    error_callback=error_callback,
                )
                consumer.start()
                # No need to close since thread starts after successful connection


def should_log_error_when_error_callback_is_none(publisher_session, caplog):
    with patch(
        "pika.adapters.blocking_connection.BlockingConnection.__init__",
        side_effect=AMQPConnectionError,
    ):
        with patch("time.sleep"):
            with pytest.raises(AMQPConnectionError):
                consumer = Consumer(
                    exchange_name=publisher_session.exchange_name,
                    queue_name=publisher_session.queue_name,
                    routing_key=publisher_session.routing_key,
                    callback=lambda x: x,
                )
                consumer.start()
                # No need to close since thread starts after successful connection

    assert caplog.record_tuples == [("pyrmq", logging.ERROR, "")]


def should_log_error_when_error_callback_fails(publisher_session, caplog):
    def error_callback(*args, **kwargs):
        raise Exception

    with patch(
        "pika.adapters.blocking_connection.BlockingConnection.__init__",
        side_effect=AMQPConnectionError,
    ):
        with patch("time.sleep"):
            with pytest.raises(AMQPConnectionError):
                consumer = Consumer(
                    exchange_name=publisher_session.exchange_name,
                    queue_name=publisher_session.queue_name,
                    routing_key=publisher_session.routing_key,
                    callback=lambda x: x,
                    error_callback=error_callback,
                )
                consumer.start()
                # No need to close since thread starts after successful connection

    assert caplog.record_tuples == [("pyrmq", logging.ERROR, "")]


def should_handle_error_when_connecting_with_infinite_retry(publisher_session):
    response = []

    def error_callback(*args, **kwargs):
        response.append(1)

    with patch(
        "pika.adapters.blocking_connection.BlockingConnection.__init__",
        side_effect=AMQPConnectionError,
    ):
        with patch("time.sleep", side_effect=[None, None, Exception]) as sleep_call:
            with pytest.raises(Exception):
                consumer = Consumer(
                    exchange_name=publisher_session.exchange_name,
                    queue_name=publisher_session.queue_name,
                    routing_key=publisher_session.routing_key,
                    callback=lambda x: x,
                    error_callback=error_callback,
                    infinite_retry=True,
                )
                consumer.start()
                # No need to close since thread starts after successful connection

    assert sleep_call.call_count == 3


@pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
def should_handle_error_when_consuming(publisher_session: Publisher):
    response = []

    def error_callback(*args, **kwargs):
        response.append(1)

    def callback(data, **kwargs):
        pass  # pragma no cover

    with patch(
        "pika.adapters.blocking_connection.BlockingChannel.basic_consume",
        side_effect=AMQPConnectionError,
    ):
        with patch("time.sleep"):
            consumer = Consumer(
                exchange_name=TEST_EXCHANGE_NAME,
                queue_name=TEST_QUEUE_NAME,
                routing_key=TEST_ROUTING_KEY,
                callback=callback,
                error_callback=error_callback,
            )
            consumer.start()

            assert_consumed_message(response, [1])
            consumer.close()


def should_get_message_with_higher_priority_in_classic_queue(
    priority_session: Publisher,
):
    """Test that messages with higher priority are delivered first in classic queues."""
    test_data = []

    for i in range(0, 10):
        rand_int = randint(0, 255)
        body = {"test": f"test{rand_int}", "priority": rand_int}
        # Use message_properties for sending priority
        priority_session.publish(body, message_properties={"priority": rand_int})
        test_data.append(body)
    response = {}

    priority_data = [
        pri_data
        for pri_data in test_data
        if pri_data["priority"] >= TEST_PRIORITY_ARGUMENTS["x-max-priority"]
    ]
    priority_data.reverse()
    less_priority_data = sorted(
        [
            pri_data
            for pri_data in test_data
            if pri_data["priority"] < TEST_PRIORITY_ARGUMENTS["x-max-priority"]
        ],
        key=lambda x: x["priority"],
    )
    priority_sorted_data = [*less_priority_data, *priority_data]
    last_expected = priority_sorted_data[0]

    def callback(data, **kwargs):
        expected = priority_sorted_data.pop()
        assert expected == data
        response.update(data)

    consumer = Consumer(
        exchange_name=priority_session.exchange_name,
        queue_name=priority_session.queue_name,
        routing_key=priority_session.routing_key,
        callback=callback,
        queue_args=TEST_PRIORITY_ARGUMENTS,
    )
    consumer.start()
    # Last message received with lowest priority
    assert_consumed_message(response, last_expected)
    consumer.close()


def should_republish_message_to_original_queue_with_dlk_retry_enabled(
    publisher_session: Publisher,
):
    body = {"test": "test"}

    publisher_session.publish(
        body, message_properties={"headers": {"x-origin": "sample"}}
    )

    response = {"count": 0}
    error_response = {"count": 0}

    def callback(data: dict, **kwargs):
        response["count"] = response["count"] + 1
        raise Exception

    def error_callback(*args, **kwargs):
        error_response["count"] = error_response["count"] + 1

    consumer = Consumer(
        exchange_name=publisher_session.exchange_name,
        queue_name=publisher_session.queue_name,
        routing_key=publisher_session.routing_key,
        callback=callback,
        is_dlk_retry_enabled=True,
        retry_interval=1,
        error_callback=error_callback,
    )
    consumer.start()
    assert_consumed_message(response, {"count": 3})
    assert_consumed_message(error_response, {"count": 3})
    consumer.close()


def should_retry_up_to_max_retries_with_proper_headers_with_dlk_retry_enabled(
    publisher_session: Publisher,
):
    body = {"test": "test"}

    publisher_session.publish(
        body, message_properties={"headers": {"x-origin": "sample"}}
    )

    new_response = {"count": 0}

    def callback(data: dict, **kwargs):
        new_response["count"] = new_response["count"] + 1
        raise Exception

    consumer = Consumer(
        exchange_name=publisher_session.exchange_name,
        queue_name=publisher_session.queue_name,
        routing_key=publisher_session.routing_key,
        callback=callback,
        is_dlk_retry_enabled=True,
        retry_interval=1,
        max_retries=1,
    )
    consumer.start()

    with pytest.raises(AssertionError):
        assert_consumed_message(new_response, {"count": 3})

    consumer.close()


def assert_consumed_infinite_loop(response, expected, tries=0, retry_after=0.6):
    if response == expected or tries > 5:
        assert response["count"] > expected["count"]
        return

    else:
        sleep(retry_after)
        return assert_consumed_infinite_loop(response, expected, tries + 1)


def should_nack_message_when_callback_method_returns_false(
    # publisher_session: Publisher,
) -> None:
    queue_name = "nack_queue_name"
    queue_args = {"x-delivery-limit": -1}

    # Create a consumer first to set up the queue
    def dummy_callback(data, **kwargs):
        pass  # pragma: no cover

    dummy_consumer = Consumer(
        exchange_name="nack_exchange_name",
        queue_name=queue_name,
        routing_key="nack_routing_key",
        callback=dummy_callback,
        queue_args=queue_args,
    )
    dummy_consumer.connect()
    dummy_consumer.declare_queue()

    # Now create the publisher
    publisher = Publisher(
        exchange_name="nack_exchange_name",
        queue_name=queue_name,
        routing_key="nack_routing_key",
        queue_args=queue_args,
    )
    channel = publisher.connect()

    body = {"test": "test"}

    publisher.publish(body, message_properties={"headers": {"x-origin": "sample"}})

    response = {"count": 0}

    def callback_that_should_nack(data: dict, **kwargs):
        response["count"] = response["count"] + 1
        return False

    consumer = Consumer(
        exchange_name=publisher.exchange_name,
        queue_name=publisher.queue_name,
        routing_key=publisher.routing_key,
        callback=callback_that_should_nack,
        queue_args=queue_args,
    )
    consumer.start()
    assert_consumed_infinite_loop(response, {"count": 1})
    consumer.close()

    # Consumer should still be able to consume the same message
    # without publishing again if nack is successful.

    new_response = {"count": 0}

    def callback_that_should_ack(data: dict, **kwargs):
        new_response["count"] = new_response["count"] + 1

    consumer = Consumer(
        exchange_name=publisher.exchange_name,
        queue_name=publisher.queue_name,
        routing_key=publisher.routing_key,
        callback=callback_that_should_ack,
        queue_args=queue_args,
    )

    consumer.start()
    assert_consumed_infinite_loop(new_response, {"count": -1})
    consumer.close()

    # Delete queue generated by Publisher on test teardown
    channel = publisher.connect()
    channel.queue_purge(queue_name)
    channel.queue_delete(queue_name)


def should_consume_with_classic_queue():
    """Test that consuming works correctly using a classic queue"""
    classic_queue_name = "classic_consumer_test_queue"

    # Create a consumer first to set up the queue
    def dummy_callback(data, **kwargs):
        pass  # pragma: no cover

    dummy_consumer = Consumer(
        exchange_name=TEST_EXCHANGE_NAME,
        queue_name=classic_queue_name,
        routing_key=TEST_ROUTING_KEY,
        callback=dummy_callback,
        queue_args={"x-queue-type": "classic"},
    )
    dummy_consumer.connect()
    dummy_consumer.declare_queue()

    # Create a publisher to send a message
    publisher = Publisher(
        exchange_name=TEST_EXCHANGE_NAME,
        queue_name=classic_queue_name,
        routing_key=TEST_ROUTING_KEY,
        queue_args={"x-queue-type": "classic"},
    )

    # Publish a test message
    test_message = {"test": "classic_consumer_test"}
    publisher.publish(test_message)

    # Create a consumer with x-queue-type=classic
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

    # Start consuming and verify the message is received
    consumer.start()
    assert_consumed_message(response, test_message)
    consumer.close()

    # Clean up
    channel = publisher.connect()
    channel.queue_purge(classic_queue_name)
    channel.queue_delete(classic_queue_name)


def should_consume_from_the_routed_queue_as_specified_in_headers() -> None:
    bound_exchange_name = "headers_exchange_name"
    routing_key = "headers_routing_key"
    first_response = {"count": 0}
    second_response = {"count": 0}

    def first_callback(data: dict, **kwargs):
        first_response["count"] = first_response["count"] + 1

    def second_callback(data: dict, **kwargs):
        second_response["count"] = second_response["count"] + 1

    # Connect and declare the first exchange/queue pair that subscribes to the bound exchange of type headers
    first_consumer = Consumer(
        exchange_name="first_exchange",
        queue_name="first_queue",
        routing_key=routing_key,
        bound_exchange={"name": bound_exchange_name, "type": "headers"},
        exchange_args={
            "routing.first": "first",
            "x-match": "all",
        },
        callback=first_callback,
    )
    first_consumer.connect()
    first_consumer.declare_queue()

    # Connect and declare the second exchange/queue pair that subscribes to the bound exchange of type headers
    second_consumer = Consumer(
        exchange_name="second_exchange",
        queue_name="second_queue",
        routing_key=routing_key,
        bound_exchange={"name": bound_exchange_name, "type": "headers"},
        exchange_args={
            "routing.second": "second",
            "x-match": "all",
        },
        callback=second_callback,
    )
    second_consumer.connect()
    second_consumer.declare_queue()

    publisher = Publisher(
        exchange_name=bound_exchange_name,
        exchange_type="headers",
        routing_key=routing_key,
    )
    publisher.publish({}, message_properties={"headers": {"routing.first": "first"}})
    publisher.publish({}, message_properties={"headers": {"routing.second": "second"}})

    first_consumer.start()
    assert_consumed_message(first_response, {"count": 1})
    first_consumer.close()

    second_consumer.start()
    assert_consumed_message(second_response, {"count": 1})
    second_consumer.close()


def should_consume_message_utf8_decoding(publisher_session: Publisher):
    consumer = Consumer(
        exchange_name=publisher_session.exchange_name,
        queue_name=publisher_session.queue_name,
        routing_key=publisher_session.routing_key,
        callback=Mock(),
    )

    data = b'{"key": "value\xe2\x80\xac"}'

    mock_channel = Mock()
    mock_method = Mock()
    mock_method.delivery_tag = "test_tag"
    mock_properties = Mock()

    consumer._consume_message(mock_channel, mock_method, mock_properties, data)


def should_respect_priority_ratio_in_quorum_queue():
    """
    Test that quorum queues respect the 2:1 ratio for high priority messages.

    This test publishes 4 messages in the following order:
    1. Normal priority
    2. High priority
    3. High priority
    4. High priority

    Expected consumption order should be:
    1. High priority
    2. High priority
    3. Normal priority (due to 2:1 ratio)
    4. High priority
    """
    # Create a unique queue name for this test
    queue_name = "quorum_priority_test_queue"
    exchange_name = "quorum_priority_exchange"
    routing_key = "quorum_priority_routing_key"

    # Create a publisher
    publisher = Publisher(
        exchange_name=exchange_name,
        queue_name=queue_name,
        routing_key=routing_key,
    )

    # Create a consumer first to ensure the queue exists
    consumed_messages = []

    def callback(data, **kwargs):
        consumed_messages.append(data)

    consumer = Consumer(
        exchange_name=exchange_name,
        queue_name=queue_name,
        routing_key=routing_key,
        callback=callback,
    )

    try:
        # Declare queue before publishing
        channel = consumer.connect()
        consumer.declare_queue()

        # Publish messages in this order: normal, high, high, high
        publisher.publish({"id": 1, "priority": "normal"})  # Normal priority
        publisher.publish(
            {"id": 2, "priority": "high"}, is_priority=True
        )  # High priority
        publisher.publish(
            {"id": 3, "priority": "high"}, is_priority=True
        )  # High priority
        publisher.publish(
            {"id": 4, "priority": "high"}, is_priority=True
        )  # High priority

        # Start consuming
        consumer.start()

        # Wait for all messages to be consumed
        sleep(3)

        # Check the consumed messages
        assert len(consumed_messages) == 4

        # Verify that the consumption order follows the 2:1 ratio for high priority messages
        # Expected order: high, high, normal, high
        assert consumed_messages[0]["id"] in [
            2,
            3,
            4,
        ]  # First message should be high priority
        assert consumed_messages[1]["id"] in [
            2,
            3,
            4,
        ]  # Second message should be high priority
        assert (
            consumed_messages[2]["id"] == 1
        )  # Third message should be normal priority
        assert consumed_messages[3]["id"] in [
            2,
            3,
            4,
        ]  # Fourth message should be high priority

        # Verify that all high priority messages were consumed
        high_priority_ids = [
            msg["id"] for msg in consumed_messages if msg["priority"] == "high"
        ]
        assert sorted(high_priority_ids) == [2, 3, 4]

    finally:
        # Clean up
        consumer.close()
        channel = publisher.connect()
        channel.queue_purge(queue_name)
        channel.queue_delete(queue_name)
