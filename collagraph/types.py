from enum import Enum


class EventLoopType(Enum):
    DEFAULT = "asyncio"
    SYNC = "sync"
