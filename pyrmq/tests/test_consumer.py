"""
    Python with RabbitMQ—simplified so you won't have to.

    :copyright: 2020-Present by Alexandre Gerona.
    :license: MIT, see LICENSE for more details.

    Full documentation is available at https://pyrmq.readthedocs.io
"""
import logging
from random import randint
from time import sleep
from unittest.mock import patch

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


def should_get_message_with_higher_priority(priority_session: Publisher):
    test_data = []

    for i in range(0, 10):
        rand_int = randint(0, 255)
        body = {"test": f"test{rand_int}", "priority": rand_int}
        priority_session.publish(body, priority=rand_int)
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
        retry_delay=1,
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
        retry_delay=1,
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
    publisher_session: Publisher,
) -> None:
    body = {"test": "test"}

    publisher_session.publish(
        body, message_properties={"headers": {"x-origin": "sample"}}
    )

    response = {"count": 0}

    def callback_that_should_nack(data: dict, **kwargs):
        response["count"] = response["count"] + 1
        return False

    consumer = Consumer(
        exchange_name=publisher_session.exchange_name,
        queue_name=publisher_session.queue_name,
        routing_key=publisher_session.routing_key,
        callback=callback_that_should_nack,
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
        exchange_name=publisher_session.exchange_name,
        queue_name=publisher_session.queue_name,
        routing_key=publisher_session.routing_key,
        callback=callback_that_should_ack,
    )

    consumer.start()
    assert_consumed_infinite_loop(response, {"count": 1})
    consumer.close()


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
