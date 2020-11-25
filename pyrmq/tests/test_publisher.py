"""
    Python with RabbitMQ—simplified so you won't have to.

    :copyright: 2020-Present by Alexandre Gerona.
    :license: MIT, see LICENSE for more details.

    Full documentation is available at https://pyrmq.readthedocs.io
"""
from unittest.mock import PropertyMock, patch

import pytest
from pika.exceptions import AMQPChannelError, AMQPConnectionError

from pyrmq.tests.conftest import TEST_EXCHANGE_NAME, TEST_QUEUE_NAME, TEST_ROUTING_KEY


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

    # Should not sleep since infinite_retry is set to False
    assert sleep.call_count == 0


def should_handle_connection_error_when_publishing():
    from pyrmq import Publisher

    def error_callback(error):
        print("error", error)

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


def should_handle_infinite_retry():
    from pyrmq import Publisher

    def error_callback(error):
        print("error", error)

    publisher = Publisher(
        exchange_name="incorrect_exchange_name",
        queue_name="incorrect_queue_name",
        routing_key="incorrect_routing_key",
        infinite_retry=True,
        error_callback=error_callback,
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
        from pyrmq import Publisher

        with patch("pika.adapters.blocking_connection.BlockingChannel.basic_publish"):
            publisher = Publisher(
                exchange_name=TEST_EXCHANGE_NAME,
                queue_name=TEST_QUEUE_NAME,
                routing_key=TEST_ROUTING_KEY,
            )
            publisher.publish({})
            publisher.publish({})
