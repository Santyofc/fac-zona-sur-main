import asyncio

import pytest


class LockedCounter:
    def __init__(self):
        self.value = 0
        self.lock = asyncio.Lock()

    async def next(self):
        async with self.lock:
            self.value += 1
            return self.value


@pytest.mark.asyncio
async def test_consecutive_generation_is_atomic_under_lock():
    counter = LockedCounter()
    values = await asyncio.gather(*[counter.next() for _ in range(50)])
    assert len(values) == len(set(values))
    assert max(values) == 50
