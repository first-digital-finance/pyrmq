"""
    Python with RabbitMQ—simplified so you won't have to.

    :copyright: 2020-Present by Alexandre Gerona.
    :license: MIT, see LICENSE for more details.

    Full documentation is available at https://pyrmq.readthedocs.io
"""

from unittest.mock import patch

import pytest
from pika.exceptions import AMQPConnectionError, AMQPChannelError
from pyrmq import Publisher


def should_handle_connection_error_when_connecting():
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
            with pytest.raises(TypeError):
                publisher.publish({})

    assert sleep.call_count == publisher.connection_attempts - 1


def should_handle_connection_error_when_publishing(publisher_session):
    body = {"sample_body": "value"}
    with patch(
        "pika.adapters.blocking_connection.BlockingChannel.basic_publish",
        side_effect=AMQPConnectionError,
    ):
        with patch("time.sleep") as sleep:
            publisher_session.publish(body)

    assert sleep.call_count == publisher_session.connection_attempts - 1


def should_handle_channel_error_when_publishing(publisher_session):
    body = {"sample_body": "value"}
    with patch(
        "pika.adapters.blocking_connection.BlockingChannel.basic_publish",
        side_effect=AMQPChannelError,
    ):
        with patch("time.sleep") as sleep:
            publisher_session.publish(body)

    assert sleep.call_count == publisher_session.connection_attempts - 1
