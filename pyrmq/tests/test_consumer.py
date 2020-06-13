"""
    Python with RabbitMQ—simplified so you won't have to.

    :copyright: 2020-Present by Alexandre Gerona.
    :license: MIT, see LICENSE for more details.

    Full documentation is available at https://pyrmq.readthedocs.io
"""

from contextlib import suppress
from time import sleep
from unittest.mock import patch

import pytest
from pika.exceptions import (
    StreamLostError,
    AMQPConnectionError,
    ConnectionWrongStateError,
    ChannelWrongStateError,
)
from pyrmq import Consumer, Publisher

possible_errors_from_channel_close = (
    StreamLostError,
    AssertionError,
    ConnectionWrongStateError,
    ChannelWrongStateError,
    AttributeError,
)


def wait_for_result(response, expected, tries=0, retry_after=0.6):
    if response == expected or tries > 5:
        assert response == expected
    else:
        sleep(retry_after)
        return wait_for_result(response, expected, tries + 1)


def should_consume_message(publisher_session: Publisher):
    body = {"test": "test"}
    publisher_session.publish(body)

    response = {}

    def callback(data):
        response.update(data)

    consumer = Consumer(
        exchange_name=publisher_session.exchange_name,
        queue_name=publisher_session.queue_name,
        routing_key=publisher_session.routing_key,
        callback=callback,
    )
    wait_for_result(response, body)
    with suppress(possible_errors_from_channel_close):
        consumer.close()


def should_handle_exception_from_callback(publisher_session: Publisher):
    body = {"test": "test"}
    publisher_session.publish(body)

    response = {}

    def callback_with_exception(data):
        response.update(data)
        raise Exception

    consumer = Consumer(
        exchange_name=publisher_session.exchange_name,
        queue_name=publisher_session.queue_name,
        routing_key=publisher_session.routing_key,
        callback=callback_with_exception,
        connection_attempts=1,
    )
    wait_for_result(response, body)
    with suppress(possible_errors_from_channel_close):
        consumer.close()


def should_handle_error_when_connecting(publisher_session):
    with patch(
        "pika.adapters.blocking_connection.BlockingConnection.__init__",
        side_effect=AMQPConnectionError,
    ):
        with patch("time.sleep") as sleep_call:
            with pytest.raises(AMQPConnectionError):
                consumer = Consumer(
                    exchange_name=publisher_session.exchange_name,
                    queue_name=publisher_session.queue_name,
                    routing_key=publisher_session.routing_key,
                    callback=lambda x: x,
                )

                # Assumes Publisher and Consumer's connection attempts are the same.
                with suppress(possible_errors_from_channel_close):
                    consumer.close()

    assert sleep_call.call_count == publisher_session.connection_attempts - 1


def should_handle_error_when_consuming(publisher_session):
    with patch(
        "pika.adapters.blocking_connection.BlockingChannel.start_consuming",
        side_effect=AMQPConnectionError,
    ):
        consumer = Consumer(
            exchange_name=publisher_session.exchange_name,
            queue_name=publisher_session.queue_name,
            routing_key=publisher_session.routing_key,
            callback=lambda x: x,
        )

        with suppress(possible_errors_from_channel_close):
            consumer.close()
