"""
    Python with RabbitMQ—simplified so you won't have to.

    :copyright: 2020-Present by Alexandre Gerona.
    :license: MIT, see LICENSE for more details.

    Full documentation is available at https://pyrmq.readthedocs.io
"""
from random import randint
from time import sleep
from unittest.mock import patch

import pytest
from pika.exceptions import AMQPConnectionError

from pyrmq import Consumer, Publisher
from pyrmq.tests.conftest import (
    TEST_ARGUMENTS,
    TEST_EXCHANGE_NAME,
    TEST_QUEUE_NAME,
    TEST_ROUTING_KEY,
)


def wait_for_result(response, expected, tries=0, retry_after=0.6):
    if response == expected or tries > 5:
        assert response == expected
        return
    else:
        sleep(retry_after)
        return wait_for_result(response, expected, tries + 1)


def should_handle_exception_from_callback(publisher_session: Publisher):
    body = {"test": "test"}
    publisher_session.publish(body)

    response = {}

    def callback(data):
        response.update(data)
        raise Exception

    consumer = Consumer(
        exchange_name=publisher_session.exchange_name,
        queue_name=publisher_session.queue_name,
        routing_key=publisher_session.routing_key,
        callback=callback,
    )
    consumer.start()
    wait_for_result(response, body)
    consumer.close()


def should_handle_error_when_connecting(publisher_session):
    response = []

    def error_callback(*args):
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


def should_handle_error_when_connecting_with_infinite_retry(publisher_session):
    response = []

    def error_callback(*args):
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


def should_handle_error_when_consuming():
    response = []

    def error_callback(*args):
        response.append(1)

    with patch(
        "pika.adapters.blocking_connection.BlockingChannel.basic_consume",
        side_effect=AMQPConnectionError,
    ):
        with patch("time.sleep"):
            consumer = Consumer(
                exchange_name=TEST_EXCHANGE_NAME,
                queue_name=TEST_QUEUE_NAME,
                routing_key=TEST_ROUTING_KEY,
                callback=lambda x: x,
                error_callback=error_callback,
            )
            consumer.start()

            wait_for_result(response, [1])
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
        if pri_data["priority"] >= TEST_ARGUMENTS["x-max-priority"]
    ]
    priority_data.reverse()
    less_priority_data = sorted(
        [
            pri_data
            for pri_data in test_data
            if pri_data["priority"] < TEST_ARGUMENTS["x-max-priority"]
        ],
        key=lambda x: x["priority"],
    )
    priority_sorted_data = [*less_priority_data, *priority_data]
    last_expected = priority_sorted_data[0]

    def callback(data):
        expected = priority_sorted_data.pop()
        assert expected == data
        response.update(data)

    consumer = Consumer(
        exchange_name=priority_session.exchange_name,
        queue_name=priority_session.queue_name,
        routing_key=priority_session.routing_key,
        callback=callback,
    )
    consumer.start()
    # Last message received with lowest priority
    wait_for_result(response, last_expected)
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

    def callback(data: dict):
        response["count"] = response["count"] + 1
        raise Exception

    def error_callback(message: str):
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
    wait_for_result(response, {"count": 3})
    wait_for_result(error_response, {"count": 3})
    consumer.close()


def should_retry_up_to_max_retries_with_proper_headers_with_dlk_retry_enabled(
    publisher_session: Publisher,
):
    body = {"test": "test"}

    publisher_session.publish(
        body, message_properties={"headers": {"x-origin": "sample"}}
    )

    new_response = {"count": 0}

    def callback(data: dict):
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
        wait_for_result(new_response, {"count": 3})
    consumer.close()
