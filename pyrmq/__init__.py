"""
    Python with RabbitMQ—simplified so you won't have to.

    :copyright: 2020-Present by Alexandre Gerona.
    :license: MIT, see LICENSE for more details.

    Full documentation is available at https://pyrmq.readthedocs.io
"""
from pkg_resources import get_distribution, DistributionNotFound

from pyrmq.consumer import Consumer
from pyrmq.publisher import Publisher

try:
    __version__ = get_distribution("pyrmq").version
except DistributionNotFound:
    __version__ = "unknown"

__all__ = [
    Consumer.__name__,
    Publisher.__name__,
]
