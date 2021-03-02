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
from pika.exceptions import AMQPChannelError, AMQPConnectionError, StreamLostError
from pika.spec import PERSISTENT_DELIVERY_MODE

CONNECTION_ERRORS = (AMQPConnectionError, ConnectionResetError, StreamLostError)
CHANNEL_ERROR = AMQPChannelError
CONNECT_ERROR = "CONNECT_ERROR"

logger = logging.getLogger("pyrmq")


class Publisher(object):
    """
    This class offers a ``BlockingConnection`` from pika that automatically handles
    queue declares and bindings plus retry logic built for its connection and publishing.
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
        :param exchange_name: Your exchange name.
        :param queue_name: Your queue name.
        :param routing_key: Your queue name.
        :param exchange_type: Exchange type to declare. Default: ``"direct"``
        :keyword host: Your RabbitMQ host. Checks env var ``RABBITMQ_HOST``. Default: ``"localhost"``
        :keyword port: Your RabbitMQ port. Checks env var ``RABBITMQ_PORT``. Default: ``5672``
        :keyword username: Your RabbitMQ username. Default: ``"guest"``
        :keyword password: Your RabbitMQ password. Default: ``"guest"``
        :keyword connection_attempts: How many times should PyRMQ try?. Default: ``3``
        :keyword retry_delay: Seconds between retries. Default: ``5``
        :keyword error_callback: Callback function to be called when connection_attempts is reached.
        :keyword infinite_retry: Tells PyRMQ to keep on retrying to publish while firing error_callback, if any. Default: ``False``
        :keyword exchange_args: Your exchange arguments. Default: ``None``
        :keyword queue_args: Your queue arguments. Default: ``None``
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
        self.retry_backoff_base = kwargs.get("retry_backoff_base", 2)
        self.retry_backoff_constant_secs = kwargs.get("retry_backoff_constant_secs", 5)
        self.error_callback = kwargs.get("error_callback")
        self.infinite_retry = kwargs.get("infinite_retry", False)
        self.exchange_args = kwargs.get("exchange_args")
        self.queue_args = kwargs.get("queue_args")

        self.connection_parameters = ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=PlainCredentials(self.username, self.password),
            connection_attempts=self.connection_attempts,
            retry_delay=self.retry_delay,
        )

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
        Creates pika's ``BlockingConnection`` from the given connection parameters.
        """
        return BlockingConnection(self.connection_parameters)

    def declare_queue(self, channel) -> None:
        """
        Declare and a bind a channel to a queue.
        :param channel: pika Channel
        """
        channel.exchange_declare(
            exchange=self.exchange_name,
            durable=True,
            exchange_type=self.exchange_type,
            arguments=self.exchange_args,
        )

        if not self.queue_name or not self.routing_key:
            return

        channel.queue_declare(
            queue=self.queue_name, arguments=self.queue_args, durable=True
        )
        channel.queue_bind(
            queue=self.queue_name,
            exchange=self.exchange_name,
            routing_key=self.routing_key,
            arguments=self.queue_args,
        )

    def connect(self, retry_count=1) -> BlockingChannel:
        """
        Creates pika's ``BlockingConnection`` and initializes queue bindings.
        :param retry_count: Amount retries the Publisher tried before sending an error message.
        """
        try:
            connection = self.__create_connection()
            channel = connection.channel()
            channel.confirm_delivery()

            self.declare_queue(channel)

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
        priority: Optional[int] = None,
        message_properties: Optional[dict] = None,
        attempt: int = 0,
        retry_count: int = 1,
    ) -> None:
        """
        Publishes data to RabbitMQ.
        :param data: Data to be published.
        :param priority: Message priority. Only works if ``x-max-priority`` is defined as queue argument.
        :param message_properties: Message properties. Default: ``{"delivery_mode": 2}``
        :param attempt: Number of attempts made.
        :param retry_count: Amount retries the Publisher tried before sending an error message.
        """
        channel = self.connect()

        try:
            message_properties = message_properties or {}
            basic_properties_kwargs = {
                "delivery_mode": PERSISTENT_DELIVERY_MODE,
                "priority": priority,
                **message_properties,
            }

            channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=self.routing_key,
                body=json.dumps(data),
                properties=BasicProperties(**basic_properties_kwargs),
                mandatory=True,
            )

        except CONNECTION_ERRORS as error:
            if not (retry_count % self.connection_attempts):
                self.__send_reconnection_error_message(error, retry_count)

                if not self.infinite_retry:
                    raise error

            time.sleep(self.retry_delay)

            self.publish(data, attempt=attempt, retry_count=(retry_count + 1))

        except CHANNEL_ERROR as error:
            if not (retry_count % self.connection_attempts):
                self.__send_reconnection_error_message(error, retry_count)

                if not self.infinite_retry:
                    raise error

            time.sleep(self.retry_delay)
            self.publish(data, attempt=attempt, retry_count=(retry_count + 1))
