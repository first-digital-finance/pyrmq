<!--suppress HtmlDeprecatedAttribute -->
<div align="center">
  <h1>PyRMQ</h1>
  <a href="https://github.com/first-digital-finance/pyrmq"><img alt="GitHub Workflow Status" src="https://img.shields.io/github/workflow/status/altusgerona/pyrmq/Test%20across%20Python%20versions?style=for-the-badge"></a>
  <a href="https://pypi.org/project/PyRMQ/"><img alt="PyPI" src="https://img.shields.io/pypi/v/pyrmq?style=for-the-badge"></a>
  <a href="https://pyrmq.readthedocs.io"><img src='https://readthedocs.org/projects/pyrmq/badge/?version=latest&style=for-the-badge' alt='Documentation Status' /></a>
  <a href="https://codecov.io/gh/first-digital-finance/pyrmq"><img alt="Codecov" src="https://img.shields.io/codecov/c/github/first-digital-finance/pyrmq/master.svg?style=for-the-badge"></a>
  <a href="https://pypi.org/project/PyRMQ/"><img alt="Supports Python >= 3.5" src="https://img.shields.io/pypi/pyversions/pyrmq?style=for-the-badge"/></a>
  <a href="https://mit-license.org" target="_blank"><img src="https://img.shields.io/badge/license-MIT-blue.svg?longCache=true&style=for-the-badge" alt="License"></a> 
  <a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg?longCache=true&style=for-the-badge"></a>
  <a href="https://github.com/PyCQA/isort"><img alt="Imports: isort" src="https://img.shields.io/badge/%20imports-isort-%231674b1?style=for-the-badge&labelColor=ef8336)](https://pycqa.github.io/isort/"></a>
  <p>Python with RabbitMQ—simplified so you won't have to.</p>
</div>

## Features
Stop worrying about boilerplating and implementing retry logic for your queues. PyRMQ already
does it for you.
- Use out-of-the-box `Consumer` and `Publisher` classes created from `pika` for your projects and tests.
- Custom DLX-DLK-based retry logic for message consumption.
- Message priorities
- Works with Python 3.
- Production ready

## Getting Started
### Installation
PyRMQ is available at PyPi.
```shell script
pip install pyrmq
```
### Usage
#### Publishing
Just instantiate the feature you want with their respective settings.
PyRMQ already works out of the box with RabbitMQ's [default initialization settings](https://hub.docker.com/_/rabbitmq).
```python
from pyrmq import Publisher
publisher = Publisher(
    exchange_name="exchange_name",
    queue_name="queue_name",
    routing_key="routing_key",
)
publisher.publish({"pyrmq": "My first message"})
```
#### Publish message with priorities
To enable prioritization of messages, instantiate your queue with the queue 
argument `x-max-priority`. It takes an integer that sets the number of possible 
priority values with a higher number commanding more priority. Then, simply 
publish your message with the priority argument specified. Any number higher 
than the set max priority is floored or considered the same.
Read more about message priorities [here](https://www.rabbitmq.com/priority.html).
```python
from pyrmq import Publisher
publisher = Publisher(
    exchange_name="exchange_name",
    queue_name="queue_name",
    routing_key="routing_key",
    queue_args={"x-max-priority": 3},
)
publisher.publish({"pyrmq": "My first message"}, priority=1)
```

| :warning: Warning                                                                                  |
|:---------------------------------------------------------------------------------------------------|
Adding arguments on an existing queue is not possible. If you wish to add queue arguments, you will need to either
delete the existing queue then recreate the queue with arguments or simply make a new queue with the arguments.

#### Consuming
Instantiating a `Consumer` automatically starts it in its own thread making it
non-blocking by default. When run after the code from before, you should be
able to receive the published data.
```python
from pyrmq import Consumer

def callback(data):
    print(f"Received {data}!")

consumer = Consumer(
    exchange_name="exchange_name",
    queue_name="queue_name",
    routing_key="routing_key",
    callback=callback
)
consumer.start()
```

#### DLX-DLK Retry Logic
What if you wanted to retry a failure on a consumed message? PyRMQ offers a custom solution that keeps your message
in queues while retrying in an [exponential backoff](https://en.wikipedia.org/wiki/Exponential_backoff) fashion.

This approach uses [dead letter exchanges and queues](https://www.rabbitmq.com/dlx.html) to republish a message to your
original queue once it has expired. PyRMQ creates this "retry" queue for you with the default naming convention of
appending your original queue with `.retry`.

```python
from pyrmq import Consumer

def callback(data):
    print(f"Received {data}!")
    raise Exception

consumer = Consumer(
    exchange_name="exchange_name",
    queue_name="queue_name",
    routing_key="routing_key",
    callback=callback,
    is_dlk_retry_enabled=True,
)
consumer.start()
```

This will start a loop of passing your message between the original queue and the retry queue until it reaches
the default number of `max_retries`.

## Documentation
Visit https://pyrmq.readthedocs.io for the most up-to-date documentation.


## Testing
For development, just run:
```shell script
pytest
```
To test for all the supported Python versions:
```shell script
pip install tox
tox
```
To test for a specific Python version:
```shell script
tox -e py38
```
