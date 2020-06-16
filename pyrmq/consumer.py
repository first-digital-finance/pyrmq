"""
    Python with RabbitMQ—simplified so you won't have to.
    This module implements PyRMQ Consumer class

    :copyright: 2020-Present by Alexandre Gerona.
    :license: MIT, see LICENSE for more details.

    Full documentation is available at https://pyrmq.readthedocs.io
"""

import logging
import os
import time

import json
from typing import Callable

from pika import PlainCredentials, ConnectionParameters, BlockingConnection
from pika.exceptions import AMQPConnectionError, ChannelClosedByBroker
from threading import Thread


logger = logging.getLogger("pyrmq")
CONNECTION_ERRORS = (AMQPConnectionError, ConnectionResetError, ChannelClosedByBroker)


class Consumer(object):
    """
    This class uses a ``BlockingConnection`` from pika that automatically handles
    queue declares and bindings plus retry logic built for its connection and consumption.
    It starts its own thread upon initialization and runs pika's ``start_consuming()``.
    """

    def __init__(
        self,
        exchange_name: str,
        queue_name: str,
        routing_key: str,
        callback: Callable,
        **kwargs,
    ):
        """
        :param exchange_name: Your exchange name.
        :param queue_name: Your queue name.
        :param routing_key: Your queue name.
        :param callback: Your callback that should handle a consumed message
        :keyword host: Your RabbitMQ host. Default: ``"localhost"``
        :keyword port: Your RabbitMQ port. Default: ``5672``
        :keyword username: Your RabbitMQ username. Default: ``"guest"``
        :keyword password: Your RabbitMQ password. Default: ``"guest"``
        :keyword connection_attempts: How many times should PyRMQ try? Default: ``3``
        :keyword retry_delay: Seconds between retries.. Default: ``5``
        :keyword retry_backoff_base: Exponential backoff base in seconds. Default: ``2``
        :keyword retry_backoff_constant_secs: Exponential backoff constant in seconds. Default: ``5``
        """
        self.connection = None
        self.exchange_name = exchange_name
        self.queue_name = queue_name
        self.routing_key = routing_key
        self.message_received_callback = callback
        self.host = kwargs.get("host") or os.getenv("RABBITMQ_HOST") or "localhost"
        self.port = kwargs.get("port") or os.getenv("RABBITMQ_PORT") or 5672
        self.username = kwargs.get("username") or "guest"
        self.password = kwargs.get("password") or "guest"
        self.connection_attempts = kwargs.get("connection_attempts") or 3
        self.retry_delay = kwargs.get("retry_delay") or 5
        self.error_callback = kwargs.get("error_callback")
        self.infinite_retry = kwargs.get("infinite_retry") or False
        self.channel = None
        self.thread = None

        self.connection_parameters = ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=PlainCredentials(self.username, self.username),
            connection_attempts=self.connection_attempts,
            retry_delay=self.retry_delay,
        )

    def start(self):
        self.connect()

        self.thread = Thread(target=self.consume)
        self.thread.setDaemon(True)
        self.thread.start()

    def __send_reconnection_error_message(self, retry_count, error) -> None:
        """
        Send error message to your preferred location.
        :param retry_count: Amount retries the Publisher tried before sending an error message.
        :param error: Error that prevented the Publisher from sending the message.
        """
        message = (
            f"Service tried to reconnect to queue **{retry_count}** times "
            f"but still failed."
            f"\n{repr(error)}"
        )
        if self.error_callback:
            self.error_callback(message)

        logger.exception(error)

    def __create_connection(self) -> BlockingConnection:
        """
        Creates a pika BlockingConnection from the given connection parameters.
        """
        return BlockingConnection(self.connection_parameters)

    def _consume_message(self, channel, method, properties, data) -> None:
        """
        Wraps the user provided callback and gracefully handles its errors and
        calling pika's ``basic_ack`` once successful.
        :param channel: pika's Channel this message was received.
        :param method: pika's basic Return
        :param properties: pika's BasicProperties
        :param data: Data received in bytes.
        """

        if isinstance(data, bytes):
            data = data.decode("ascii")

        data = json.loads(data)

        try:
            logger.debug("Received message from queue")

            self.message_received_callback(data)

        except Exception as error:
            logger.exception(error)

        channel.basic_ack(delivery_tag=method.delivery_tag)

    def connect(self, retry_count=1) -> None:
        """
        Creates a BlockingConnection from pika and initializes queue bindings.
        :param retry_count: Amount retries the Publisher tried before sending an error message.
        """
        try:
            self.connection = self.__create_connection()
            self.channel = self.connection.channel()

        except CONNECTION_ERRORS as error:
            if not (retry_count % self.connection_attempts):
                self.__send_reconnection_error_message(retry_count, error)
                if not self.infinite_retry:
                    raise error

            time.sleep(self.retry_delay)

            self.connect(retry_count=(retry_count + 1))

    def close(self) -> None:
        """
        Manually closes a connection to RabbitMQ. Useful for debugging and tests.
        """
        self.thread.join(0.1)

    def consume(self, retry_count=1) -> None:
        """
        Wraps pika's ``basic_consume()`` and ``start_consuming()`` with retry logic.
        """
        try:
            self.channel.basic_consume(self.queue_name, self._consume_message)

            self.channel.start_consuming()

        except CONNECTION_ERRORS as error:
            if not (retry_count % self.connection_attempts):
                self.__send_reconnection_error_message(retry_count, error)
                if not self.infinite_retry:
                    raise error

            time.sleep(self.retry_delay)

            self.connect()
            self.consume(retry_count=(retry_count + 1))
