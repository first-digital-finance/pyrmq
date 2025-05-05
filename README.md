<!--suppress HtmlDeprecatedAttribute -->
<div align="center">
  <h1>PyRMQ</h1>
  <a href="https://github.com/first-digital-finance/pyrmq"><img alt="GitHub Workflow Status" src="https://img.shields.io/github/actions/workflow/status/first-digital-finance/pyrmq/testing.yml?branch=master&style=for-the-badge"></a>
  <a href="https://pypi.org/project/PyRMQ/"><img alt="PyPI" src="https://img.shields.io/pypi/v/pyrmq?style=for-the-badge"></a>
  <a href="https://pyrmq.readthedocs.io"><img src='https://readthedocs.org/projects/pyrmq/badge/?version=latest&style=for-the-badge' alt='Documentation Status' /></a>
  <a href="https://codecov.io/gh/first-digital-finance/pyrmq"><img alt="Codecov" src="https://img.shields.io/codecov/c/github/first-digital-finance/pyrmq/master.svg?style=for-the-badge"></a>
  <a href="https://pypi.org/project/PyRMQ/"><img alt="Supports Python >= 3.11" src="https://img.shields.io/pypi/pyversions/pyrmq?style=for-the-badge"/></a>
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
- Works with Python 3.11-3.13.
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

> **Note:** The Publisher class only verifies that exchanges exist and does not create queues or exchanges.
> Exchanges must be created by a Consumer before a Publisher can use them.

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
PyRMQ supports two ways to prioritize messages:

1. **Quorum queues (recommended)**: Use the `is_priority` flag to set a priority of 5 (high priority).
   ```python
   from pyrmq import Publisher
   publisher = Publisher(
       exchange_name="exchange_name",
       queue_name="queue_name",
       routing_key="routing_key",
   )
   publisher.publish({"pyrmq": "High priority message"}, is_priority=True)  # Priority 5
   publisher.publish({"pyrmq": "Normal message"})  # Default priority 0
   ```
   
   In quorum queues, messages with priority 5-255 are considered high priority, and those with priority 0-4 are normal priority. When both types exist in the queue, RabbitMQ maintains a 2:1 ratio, delivering at least 2 high priority messages for every 1 normal priority message.

2. **Classic queues**: For finer-grained control with numeric priorities, configure your Consumer with the `x-max-priority` 
   argument and use message properties when publishing.
   ```python
   # When setting up the Consumer
   consumer = Consumer(
       exchange_name="exchange_name",
       queue_name="queue_name",
       routing_key="routing_key",
       queue_args={"x-queue-type": "classic", "x-max-priority": 5},
       callback=callback
   )
   
   # When publishing
   publisher.publish({"pyrmq": "Priority message"}, message_properties={"priority": 3})
   ```

Read more about message priorities [here](https://www.rabbitmq.com/docs/priority).

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
in queues while retrying periodically for a set amount of times.

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

##### DLX-DLK Retry backoff vs Periodic retries
Since [RabbitMQ does not remove expired messages that aren't at the head of the queue](https://www.rabbitmq.com/ttl.html#per-message-ttl-caveats),
this leads to a congestion of the retry queue that is bottlenecked with an unexpired message
at the head. As such, as of 3.3.0, PyRMQ will be using a simple periodic retry.

#### Using other exchange types
You can use another exchange type just by simply specifying it in the Publisher class. The default is
`direct`. 

```python
from pyrmq import Publisher

queue_args = {"routing.sample": "sample", "x-match": "all"}

publisher = Publisher(
    exchange_name="exchange_name",
    exchange_type="headers",
    queue_args=queue_args
)

message_properties = {"headers": {"routing.sample": "sample"}}
publisher.publish({"pyrmq": "My first message"}, message_properties=message_properties)
```

This is an example of how to publish to a headers exchange that will get routed
based on its headers.

#### Binding an exchange to another exchange
By default, the `exchange_name` you pass when initializing a `Consumer` is declared and bound to the passed
`queue_name`. What if you want to bind and declare this exchange to another exchange as well?

This is done by using `bound_exchange`. This parameter accepts an object with two keys: `name` of your exchange and its
`type`. Let's take a look at an example to see this in action.

```py
from pyrmq import Consumer

def callback(data):
    print(f"Received {data}!")
    raise Exception

consumer = Consumer(
    exchange_name="direct_exchange",
    queue_name="direct_queue",
    routing_key="routing_key",
    bound_exchange={"name": "headers_exchange_name", "type": "headers"},
    callback=callback,
    is_dlk_retry_enabled=True,
)
consumer.start()
```

In the example above, we want to consume from an exchange called `direct_exchange` that is directly bound to queue
`direct_queue`. We want `direct_exchange` to get its messages from another exchange called `headers_exchange_name` of
type `headers`. By using `bound_exchange`, PyRMQ declares `direct_exchange` and `direct_queue` along with any queue or
exchange arguments you may have _first_ then declares the bound exchange next and binds them together. This is done
to alleviate the need to declare your bound exchange manually.

| :warning: Important                                                                                |
|:---------------------------------------------------------------------------------------------------|
Since this method uses [e2e bindings](https://www.rabbitmq.com/e2e.html), if you're using a headers exchange to bind your consumer to, they _and_ your publisher must all have the same routing key to route the messages properly. This is not needed for exchange to queue bindings as the routing key is optional for those.

#### Declaring _classic_ queues

The default queue type when declaring is quorum which has the advantage of data replication and being highly available. Though these features fit better for highly distributed enterprise systems, it may not fit your certain requirements. You may read more about the differences between the classic and quorum queue types in the official [documentation](https://www.rabbitmq.com/docs/quorum-queues).

To configure your queue to classic, simply instantiate your queue with the queue argument `x-queue-type` and set its value to `classic`.
```python
from pyrmq import Publisher
publisher = Publisher(
    exchange_name="exchange_name",
    queue_name="queue_name",
    routing_key="routing_key",
    queue_args={"x-queue-type": "classic"},
)
```


## Documentation
Visit https://pyrmq.readthedocs.io for the most up-to-date documentation.


## Testing
For development, just run:
```shell script
pytest
```
To test for all the supported Python versions using UV:
```shell script
uv tool install tox --with tox-uv 
tox
```
To test for a specific Python version:
```shell script
tox -e py311
```

## Development with UV

This project uses [UV](https://github.com/astral-sh/uv), a fast Python package installer and resolver written in Rust.

### Basic Setup

```shell script
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a virtual environment (uses current Python version)
uv venv

# Activate the virtual environment
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install the package with development dependencies
uv add -e .[dev]

# Run tests
uv run pytest
```

### Working with Multiple Python Versions

```shell script
# List available Python versions
uv python list

# Install a specific Python version
uv python install 3.8.19

# Create a virtual environment with a specific Python version
uv venv --python 3.8

# Build with a specific Python version
uv build --python 3.9

# Run tests with a specific Python version
uv run --python 3.11 pytest
```

### Building and Publishing

```shell script
# Build the package
uv build

# Publish to PyPI (requires a token)
uv publish --token YOUR_PYPI_TOKEN
```
