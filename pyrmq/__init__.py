"""
    Python with RabbitMQ—simplified so you won't have to.

    :copyright: 2020-Present by Alexandre Gerona.
    :license: MIT, see LICENSE for more details.

    Full documentation is available at https://pyrmq.readthedocs.io
"""
from pkg_resources import get_distribution

from pyrmq.consumer import Consumer
from pyrmq.publisher import Publisher

__version__ = get_distribution("pyrmq").version

__all__ = [
    Consumer.__name__,
    Publisher.__name__,
]
