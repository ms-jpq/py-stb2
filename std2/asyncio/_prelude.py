from asyncio import get_running_loop
from asyncio.coroutines import iscoroutine
from asyncio.futures import Future
from asyncio.tasks import FIRST_COMPLETED, gather, wait
from functools import partial
from itertools import chain
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
)

from ..types import Void, VoidType
from .go import GO, go

T = TypeVar("T")
U = TypeVar("U")


async def pure(item: T) -> T:
    return item


async def anext(
    ait: AsyncIterator[T], default: Union[U, VoidType] = Void
) -> Union[T, U]:
    if default is Void:
        return await ait.__anext__()
    else:
        try:
            return await ait.__anext__()
        except StopAsyncIteration:
            return cast(U, default)


async def race(
    aw: Awaitable[T], *aws: Awaitable[T], go: GO = go
) -> Tuple[T, Sequence[Future[T]]]:
    futs = await gather(
        *(go(a) if iscoroutine(a) else pure(a) for a in chain((aw,), aws))
    )
    done, pending = await wait(futs, return_when=FIRST_COMPLETED)
    ret = done.pop().result()
    return ret, tuple(chain(done, pending))


async def run_in_executor(f: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    loop = get_running_loop()
    cont = partial(f, *args, **kwargs)
    return await loop.run_in_executor(None, cont)
