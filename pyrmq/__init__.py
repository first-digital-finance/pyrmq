"""
    Python with RabbitMQ—simplified so you won't have to.

    :copyright: 2020-Present by Alexandre Gerona.
    :license: MIT, see LICENSE for more details.

    Full documentation is available at https://pyrmq.readthedocs.io
"""

from importlib.metadata import version

from pyrmq.consumer import Consumer
from pyrmq.publisher import Publisher

try:
    __version__ = version("pyrmq")
except Exception:  # pragma: no cover
    __version__ = "unknown"

__all__ = [
    Consumer.__name__,
    Publisher.__name__,
]
