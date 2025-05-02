"""
    Python with RabbitMQ—simplified so you won't have to.
    This module implements PyRMQ Publisher class

    :copyright: 2020-Present by Alexandre Gerona.
    :license: MIT, see LICENSE for more details.

    Full documentation is available at https://pyrmq.readthedocs.io
"""

import json
import logging
import os
import time
from typing import Optional

from pika import (
    BasicProperties,
    BlockingConnection,
    ConnectionParameters,
    PlainCredentials,
)
from pika.adapters.blocking_connection import BlockingChannel
from pika.adapters.utils.connection_workflow import AMQPConnectorException
from pika.exceptions import (
    AMQPChannelError,
    AMQPConnectionError,
    ChannelClosedByBroker,
    StreamLostError,
    UnroutableError,
)
from pika.spec import PERSISTENT_DELIVERY_MODE

CONNECTION_ERRORS = (
    AMQPConnectionError,
    AMQPConnectorException,
    AMQPChannelError,
    ConnectionResetError,
    ChannelClosedByBroker,
    ConnectionError,
    StreamLostError,
)
CONNECT_ERROR = "CONNECT_ERROR"

logger = logging.getLogger("pyrmq")


class Publisher(object):
    """
    This class uses a ``BlockingConnection`` from pika for publishing messages to RabbitMQ.

    Important Note:
    This class does not declare or bind queues. It only verifies that exchanges exist but will not
    create them. Consumers should declare exchanges and queues before publishers attempt to use them.
    If you try to publish to a non-existent exchange, a ChannelClosedByBroker exception will be raised.
    """

    def __init__(
        self,
        exchange_name: str,
        queue_name: Optional[str] = "",
        routing_key: Optional[str] = "",
        exchange_type: Optional[str] = "direct",
        **kwargs,
    ):
        """
        :param exchange_name: The exchange name to publish to (must already exist).
        :param queue_name: The queue name (used only for routing key if routing_key is empty).
        :param routing_key: The routing key for message delivery. If blank, queue_name is used.
        :param exchange_type: Exchange type to verify. Default: ``"direct"``
        :keyword host: Your RabbitMQ host. Checks env var ``RABBITMQ_HOST``. Default: ``"localhost"``
        :keyword port: Your RabbitMQ port. Checks env var ``RABBITMQ_PORT``. Default: ``5672``
        :keyword username: Your RabbitMQ username. Default: ``"guest"``
        :keyword password: Your RabbitMQ password. Default: ``"guest"``
        :keyword connection_attempts: How many times should PyRMQ try?. Default: ``3``
        :keyword retry_delay: Seconds between connection retries. Default: ``5``
        :keyword error_callback: Callback function to be called when connection_attempts is reached.
        :keyword infinite_retry: Tells PyRMQ to keep on retrying to publish while firing error_callback, if any. Default: ``False``
        :keyword exchange_args: Exchange arguments for verification. Default: ``None``
        :keyword queue_args: Queue arguments for message properties. Default: ``{}``

        .. note::
           This class no longer creates queues or exchanges. The exchange must exist before publishing,
           and the Consumer class should be used to declare exchanges and queues.
        """

        self.exchange_name = exchange_name
        self.queue_name = queue_name
        self.routing_key = routing_key
        self.exchange_type = exchange_type
        self.host = kwargs.get("host") or os.getenv("RABBITMQ_HOST") or "localhost"
        self.port = kwargs.get("port") or os.getenv("RABBITMQ_PORT") or 5672
        self.username = kwargs.get("username", "guest")
        self.password = kwargs.get("password", "guest")
        self.connection_attempts = kwargs.get("connection_attempts", 3)
        self.retry_delay = kwargs.get("retry_delay", 5)
        self.error_callback = kwargs.get("error_callback")
        self.infinite_retry = kwargs.get("infinite_retry", False)
        self.exchange_args = kwargs.get("exchange_args")
        self.queue_args = kwargs.get("queue_args", {})

        self.connection_parameters = ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=PlainCredentials(self.username, self.password),
            connection_attempts=self.connection_attempts,
            retry_delay=self.retry_delay,
        )

        if "x-queue-type" not in self.queue_args:
            self.queue_args["x-queue-type"] = "quorum"

        self.connections = {}

    def __send_reconnection_error_message(self, error, retry_count) -> None:
        """
        Send error message to your preferred location.
        :param error: Error that prevented the Publisher from sending the message.
        :param retry_count: Amount retries the Publisher tried before sending an error message.
        """
        message = (
            f"Service tried to reconnect to queue **{retry_count}** times "
            f"but still failed."
            f"\n{repr(error)}"
        )

        if self.error_callback:
            try:
                self.error_callback(message, error=error, error_type=CONNECT_ERROR)

            except Exception as exception:
                logger.exception(exception)

        else:
            logger.exception(error)

    def __create_connection(self) -> BlockingConnection:
        """
        Create pika's ``BlockingConnection`` from the given connection parameters.
        """
        return BlockingConnection(self.connection_parameters)

    def verify_exchange(self, channel) -> None:
        """
        Verifies that an exchange exists using passive mode.
        This will raise an exception if the exchange doesn't exist.

        :param channel: pika Channel
        :raises: ChannelClosedByBroker if the exchange doesn't exist
        """
        # Always use passive mode to only check if exchange exists
        channel.exchange_declare(
            exchange=self.exchange_name,
            durable=True,
            exchange_type=self.exchange_type,
            arguments=self.exchange_args,
            passive=True,  # Only check if exchange exists, don't create it
        )

    def connect(self, retry_count=1) -> BlockingChannel:
        """
        Create pika's ``BlockingConnection`` and verify the exchange exists.
        :param retry_count: Amount retries the Publisher tried before sending an error message.
        :raises: ChannelClosedByBroker if the exchange doesn't exist
        """
        try:
            connection = self.__create_connection()
            channel = connection.channel()
            channel.confirm_delivery()

            self.verify_exchange(channel)

            return channel

        except CONNECTION_ERRORS as error:
            if not (retry_count % self.connection_attempts):
                self.__send_reconnection_error_message(
                    error, self.connection_attempts * retry_count
                )

                if not self.infinite_retry:
                    raise error

            time.sleep(self.retry_delay)

            return self.connect(retry_count=(retry_count + 1))

    def publish(
        self,
        data: dict,
        message_properties: Optional[dict] = None,
        is_priority: bool = False,
        attempt: int = 0,
        retry_count: int = 1,
    ) -> None:
        """
        Publish data to RabbitMQ.
        :param data: Data to be published.
        :param message_properties: Message properties. Default: ``{"delivery_mode": 2}``.
            For classic queues with the ``x-max-priority`` argument, use ``{"priority": N}``.
        :param is_priority: For quorum queues, marks the message as high priority when True.
        :param attempt: Number of attempts made.
        :param retry_count: Amount retries the Publisher tried before sending an error message.
        """
        channel = self.connect()

        try:
            message_properties = message_properties or {}

            # Handle priorities for quorum queues
            if is_priority:
                # For quorum queues, high priority is 5-255 (we use 5)
                # Messages with priority 0-4 are normal priority (0 is default)
                message_properties["priority"] = 5

            basic_properties_kwargs = {
                "delivery_mode": PERSISTENT_DELIVERY_MODE,
                **message_properties,
            }

            try:
                channel.basic_publish(
                    exchange=self.exchange_name,
                    routing_key=self.routing_key
                    or self.queue_name,  # Fall back to queue_name if routing_key is empty
                    body=json.dumps(data),
                    properties=BasicProperties(**basic_properties_kwargs),
                    mandatory=True,
                )
            except UnroutableError:
                # When a message is published with mandatory=True but can't be routed
                # This might happen if the queue doesn't exist or isn't bound to the exchange
                logger.warning(
                    f"Message could not be routed to any queue. Exchange: {self.exchange_name}, "
                    f"Routing key: {self.routing_key or self.queue_name}"
                )
                # Re-raise to maintain backward compatibility
                raise

        except CONNECTION_ERRORS as error:
            if not (retry_count % self.connection_attempts):
                self.__send_reconnection_error_message(error, retry_count)

                if not self.infinite_retry:
                    raise error

            time.sleep(self.retry_delay)

            self.publish(data, attempt=attempt, retry_count=(retry_count + 1))
