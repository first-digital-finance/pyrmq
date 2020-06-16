"""
    Python with RabbitMQ—simplified so you won't have to.

    :copyright: 2020-Present by Alexandre Gerona.
    :license: MIT, see LICENSE for more details.

    Full documentation is available at https://pyrmq.readthedocs.io
"""

from time import sleep
from unittest.mock import patch

import pytest
from pika.exceptions import AMQPConnectionError
from pyrmq import Consumer, Publisher
from pyrmq.tests.conftest import TEST_EXCHANGE_NAME, TEST_QUEUE_NAME, TEST_ROUTING_KEY


def wait_for_result(response, expected, tries=0, retry_after=0.6):
    if response == expected or tries > 5:
        assert response == expected
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
