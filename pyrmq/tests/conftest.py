"""
    Python with RabbitMQ—simplified so you won't have to.

    :copyright: 2020-Present by Alexandre Gerona.
    :license: MIT, see LICENSE for more details.

    Full documentation is available at https://pyrmq.readthedocs.io
"""
from contextlib import suppress

import pytest
from pika import BlockingConnection

from pyrmq import Publisher

TEST_EXCHANGE_NAME = "sample_exchange"
TEST_QUEUE_NAME = "test_queue_name"
TEST_ROUTING_KEY = "test_routing_key"

TEST_PRIORITY_EXCHANGE_NAME = "sample_priority_exchange"
TEST_PRIORITY_QUEUE_NAME = "sample_priority_queue_name"
TEST_PRIORITY_ROUTING_KEY = "sample_priority_routing_key"
TEST_PRIORITY_ARGUMENTS = {"x-max-priority": 5, "x-queue-type": "classic"}


def create_queue(channel, publisher):
    channel.queue_declare(
        queue=publisher.queue_name,
        arguments=publisher.queue_args,
        durable=True,
    )

    return channel


def create_exchange(channel, publisher):
    channel.exchange_declare(
        exchange=publisher.exchange_name,
        durable=True,
        exchange_type=publisher.exchange_type,
    )

    return channel


def create_queue_and_exchange(publisher):
    """Create a new queue and exchange for the publisher."""
    channel = BlockingConnection(publisher.connection_parameters).channel()
    create_exchange(channel, publisher)
    create_queue(channel, publisher)
    channel.close()


def cleanup_queue_and_exchange(publisher):
    """Clean up the queue and exchange created for the publisher."""
    channel = BlockingConnection(publisher.connection_parameters).channel()
    with suppress(Exception):
        channel.queue_purge(publisher.queue_name)
        channel.queue_delete(publisher.queue_name)
        channel.exchange_delete(publisher.exchange_name)
    channel.close()


@pytest.fixture(scope="function")
def publisher_session():
    """Create a new publisher with test queue and exchange names."""
    publisher = Publisher(
        exchange_name=TEST_EXCHANGE_NAME,
        queue_name=TEST_QUEUE_NAME,
        routing_key=TEST_ROUTING_KEY,
    )

    # Create queue and exchange before returning the publisher
    create_queue_and_exchange(publisher)

    yield publisher

    # Clean up after the test
    cleanup_queue_and_exchange(publisher)


@pytest.fixture(scope="function")
def priority_publisher_session():
    """Create a new priority publisher with test queue and exchange names."""
    publisher = Publisher(
        exchange_name=TEST_PRIORITY_EXCHANGE_NAME,
        queue_name=TEST_PRIORITY_QUEUE_NAME,
        routing_key=TEST_PRIORITY_ROUTING_KEY,
        queue_args=TEST_PRIORITY_ARGUMENTS,
    )

    # Create queue and exchange before returning the publisher
    create_queue_and_exchange(publisher)

    yield publisher

    # Clean up after the test
    cleanup_queue_and_exchange(publisher)


@pytest.fixture(scope="function", autouse=True)
def clean_specific_queues():
    """Clean up any remaining queues and exchanges after each test."""
    yield
    # This fixture is now empty as cleanup is handled in the individual publisher fixtures
