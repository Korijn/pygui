import asyncio
import gc
import textwrap

import pytest
from observ import scheduler
from observ.proxy_db import proxy_db

from collagraph.sfc import compiler

# If there is no current event loop, then get_event_loop()
# will emit a deprecation warning since Python 3.12, which
# will be turned into an error for future versions of Python.
# https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.get_event_loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


async def miniloop():
    await asyncio.sleep(0)

def load(source, namespace=None):
    source = textwrap.dedent(source)
    return compiler.load_from_string(source, namespace=namespace)


@pytest.fixture
def parse_source():
    yield load


@pytest.fixture(autouse=True)
def cleanup():
    """Cleanup steps copied over observ test suite"""
    gc.collect()
    proxy_db.db = {}

    yield

    scheduler.clear()


@pytest.fixture
def process_events():
    loop = asyncio.get_event_loop_policy().get_event_loop()

    def run():
        loop.run_until_complete(miniloop())

    yield run

    loop.close()
