"""
    Python with RabbitMQ—simplified so you won't have to.
    This module implements PyRMQ Consumer class

    :copyright: 2020-Present by Alexandre Gerona.
    :license: MIT, see LICENSE for more details.

    Full documentation is available at https://pyrmq.readthedocs.io
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from threading import Thread
from typing import Callable, Optional, Union

from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from pika.exceptions import AMQPConnectionError, ChannelClosedByBroker

CONNECTION_ERRORS = (AMQPConnectionError, ConnectionResetError, ChannelClosedByBroker)
CONNECT_ERROR = "CONNECT_ERROR"
CONSUME_ERROR = "CONSUME_ERROR"

logger = logging.getLogger("pyrmq")


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
        exchange_type: Optional[str] = "direct",
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
        :keyword is_dlk_retry_enabled: Flag to enable DLK-based retry logic of consumed messages. Default: ``False``
        :keyword retry_delay: Seconds between retries. Default: ``5``
        :keyword retry_backoff_base: Exponential backoff base in seconds. Default: ``2``
        :keyword retry_queue_suffix: The suffix that will be appended to the ``queue_name`` to act as the name of the retry_queue. Default: ``retry``
        :keyword max_retries: Number of maximum retries for DLK retry logic. Default: ``20``
        :keyword exchange_args: Your exchange arguments. Default: ``None``
        :keyword queue_args: Your queue arguments. Default: ``None``
        :keyword bound_exchange: The exchange this consumer needs to bind to. This is an object that has two keys, ``name`` and ``type``. Default: ``None``
        :keyword auto_ack: Flag whether to ack or nack the consumed message regardless of its outcome. Default: ``True``
        :keyword prefetch_count: How many messages should the consumer retrieve at a time for consumption. Default: ``1``
        """

        from pyrmq import Publisher

        self.connection = None
        self.exchange_name = exchange_name
        self.queue_name = queue_name
        self.routing_key = routing_key
        self.exchange_type = exchange_type
        self.message_received_callback = callback
        self.host = kwargs.get("host") or os.getenv("RABBITMQ_HOST") or "localhost"
        self.port = kwargs.get("port") or os.getenv("RABBITMQ_PORT") or 5672
        self.username = kwargs.get("username", "guest")
        self.password = kwargs.get("password", "guest")
        self.connection_attempts = kwargs.get("connection_attempts", 3)
        self.retry_delay = kwargs.get("retry_delay", 5)
        self.is_dlk_retry_enabled = kwargs.get("is_dlk_retry_enabled", False)
        self.retry_backoff_base = kwargs.get("retry_backoff_base", 2)
        self.retry_queue_suffix = kwargs.get("retry_queue_suffix", "retry")
        self.max_retries = kwargs.get("max_retries", 20)
        self.error_callback = kwargs.get("error_callback")
        self.infinite_retry = kwargs.get("infinite_retry", False)
        self.exchange_args = kwargs.get("exchange_args")
        self.queue_args = kwargs.get("queue_args")
        self.bound_exchange = kwargs.get("bound_exchange")
        self.auto_ack = kwargs.get("auto_ack", True)
        self.prefetch_count = kwargs.get("prefetch_count", 1)
        self.channel = None
        self.thread = None

        self.connection_parameters = ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=PlainCredentials(self.username, self.password),
            connection_attempts=self.connection_attempts,
            retry_delay=self.retry_delay,
        )

        self.retry_queue_name = f"{self.queue_name}.{self.retry_queue_suffix}"

        if self.is_dlk_retry_enabled:
            self.retry_publisher = Publisher(
                exchange_name=self.retry_queue_name,
                queue_name=self.retry_queue_name,
                routing_key=self.retry_queue_name,
                username=self.username,
                password=self.password,
                port=self.port,
                host=self.host,
                queue_args={
                    "x-dead-letter-exchange": self.exchange_name,
                    "x-dead-letter-routing-key": self.routing_key,
                },
            )

    def declare_queue(self) -> None:
        """
        Declare and a bind a channel to a queue.
        """
        self.channel.exchange_declare(
            exchange=self.exchange_name,
            durable=True,
            exchange_type=self.exchange_type,
            arguments=self.exchange_args,
        )

        self.channel.queue_declare(
            queue=self.queue_name, arguments=self.queue_args, durable=True
        )
        self.channel.queue_bind(
            queue=self.queue_name,
            exchange=self.exchange_name,
            routing_key=self.routing_key,
            arguments=self.queue_args,
        )

        if self.bound_exchange:
            bound_exchange_name = self.bound_exchange["name"]
            bound_exchange_type = self.bound_exchange["type"]
            self.channel.exchange_declare(
                exchange=bound_exchange_name,
                durable=True,
                exchange_type=bound_exchange_type,
            )
            self.channel.exchange_bind(
                destination=self.exchange_name,
                source=bound_exchange_name,
                routing_key=self.routing_key,
                arguments=self.exchange_args,
            )

    def start(self):
        self.connect()
        self.declare_queue()

        self.thread = Thread(target=self.consume)
        self.thread.setDaemon(True)
        self.thread.start()

    def __run_error_callback(
        self, message: str, error: Exception, error_type: str
    ) -> None:
        """
        Log error message
        :param message: Message to be logged in error_callback
        :param error: Error encountered in consuming the message
        :param error_type: Type of error (CONNECT_ERROR or CONSUME_ERROR)
        """
        if self.error_callback:
            try:
                self.error_callback(message, error=error, error_type=error_type)

            except Exception as exception:
                logger.exception(exception)

        else:
            logger.exception(error)

    def __send_reconnection_error_message(
        self,
        error: Union[AMQPConnectionError, ConnectionResetError, ChannelClosedByBroker],
        retry_count: int,
    ) -> None:
        """
        Send error message to your preferred location.
        :param error: Error that prevented the Consumer from processing the message.
        :param retry_count: Amount retries the Consumer tried before sending an error message.
        """
        message = (
            f"Service tried to reconnect to queue **{retry_count}** times "
            f"but still failed."
            f"\n{repr(error)}"
        )
        self.__run_error_callback(message, error, CONNECT_ERROR)

    def __send_consume_error_message(
        self, error: Exception, retry_count: int = 1
    ) -> None:
        """
        Send error message to your preferred location.
        :param error: Error that prevented the Consumer from processing the message.
        :param retry_count: Amount retries the Consumer tried before sending an error message.
        """
        message = (
            f"Service tried to consume message **{retry_count}** times "
            f"but still failed."
            f"\n{repr(error)}"
        )
        self.__run_error_callback(message, error, CONSUME_ERROR)

    def __create_connection(self) -> BlockingConnection:
        """
        Creates a pika BlockingConnection from the given connection parameters.
        """
        return BlockingConnection(self.connection_parameters)

    def _compute_expiration(self, retry_count: int) -> int:
        """
        Computes message expiration time from the retry queue in seconds.
        """
        b = self.retry_backoff_base
        n = self.retry_delay * 1000

        return b ** (retry_count - 1) * n  # 5, 10, 20, 40, 80

    def _publish_to_retry_queue(
        self, data: dict, properties, retry_reason: Exception
    ) -> None:
        """
        Publishes message to retry queue with the appropriate metadata in the headers.
        """
        headers = properties.headers or {}
        attempt = headers.get("x-attempt", 0) + 1
        self.__send_consume_error_message(retry_reason, attempt)

        if attempt > self.max_retries:
            return

        expiration = self._compute_expiration(attempt)
        now = datetime.now()
        next_attempt = now + timedelta(seconds=(expiration // 1000))
        message_properties = {
            **properties.__dict__,
            "expiration": str(expiration),
            "headers": {
                **headers,
                "x-attempt": attempt,
                "x-max-attempts": self.max_retries,
                "x-created-at": headers.get("x-created-at", now.isoformat()),
                "x-retry-reason": repr(retry_reason),
                "x-next-attempt": next_attempt.isoformat(),
            },
        }

        for i in range(1, attempt + 1):
            attempt_no = f"x-attempt-{i}"
            previous_attempts = message_properties["headers"]
            previous_attempts[attempt_no] = previous_attempts.get(
                attempt_no, now.isoformat()
            )

        self.retry_publisher.publish(data, message_properties=message_properties)

    def _consume_message(self, channel, method, properties, data: dict) -> None:
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

        auto_ack = None

        try:
            logger.debug("Received message from queue")

            auto_ack = self.message_received_callback(
                data, channel=channel, method=method, properties=properties
            )

        except Exception as error:
            if self.is_dlk_retry_enabled:
                self._publish_to_retry_queue(data, properties, error)

            else:
                self.__send_consume_error_message(error)

        if auto_ack or (auto_ack is None and self.auto_ack):
            channel.basic_ack(delivery_tag=method.delivery_tag)

        else:
            channel.basic_nack(delivery_tag=method.delivery_tag)

    def connect(self, retry_count=1) -> None:
        """
        Creates a BlockingConnection from pika and initializes queue bindings.
        :param retry_count: Amount retries the Publisher tried before sending an error message.
        """
        try:
            self.connection = self.__create_connection()
            self.channel = self.connection.channel()
            self.channel.basic_qos(prefetch_count=self.prefetch_count)

        except CONNECTION_ERRORS as error:
            if not (retry_count % self.connection_attempts):
                self.__send_reconnection_error_message(
                    error, self.connection_attempts * retry_count
                )

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
                self.__send_reconnection_error_message(error, retry_count)

                if not self.infinite_retry:
                    raise error

            time.sleep(self.retry_delay)

            self.connect()
            self.consume(retry_count=(retry_count + 1))
