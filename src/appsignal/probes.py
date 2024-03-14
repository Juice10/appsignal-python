from __future__ import annotations

import logging
from inspect import signature
from threading import Thread
from time import gmtime, sleep
from typing import Any, Callable, NoReturn, Optional, TypeVar, Union, cast


T = TypeVar("T")

Probe = Union[Callable[[], None], Callable[[Optional[T]], Optional[T]]]

_probes: dict[str, Probe] = {}
_probe_states: dict[str, Any] = {}


def start_probes() -> None:
    Thread(target=_start_probes, daemon=True).start()


def _start_probes() -> NoReturn:
    sleep(_initial_wait_time())

    while True:
        _run_probes()
        sleep(_wait_time())


def _run_probes() -> None:
    for name in _probes:
        _run_probe(name)


def _run_probe(name: str) -> None:
    logger = logging.getLogger("appsignal")
    logger.debug(f"Gathering minutely metrics with `{name}` probe")

    try:
        probe = _probes[name]

        if len(signature(probe).parameters) > 0:
            probe = cast(Callable[[Any], Any], probe)
            state = _probe_states.get(name)
            result = probe(state)
            _probe_states[name] = result
        else:
            probe = cast(Callable[[], None], probe)
            probe()

    except Exception as e:
        logger.debug(f"Error in minutely probe `{name}`: {e}")


def _wait_time() -> int:
    return 60 - gmtime().tm_sec


def _initial_wait_time() -> int:
    remaining_seconds = _wait_time()
    if remaining_seconds > 30:
        return remaining_seconds

    return remaining_seconds + 60


def register(name: str, probe: Probe) -> None:
    if name in _probes:
        logger = logging.getLogger("appsignal")
        logger.debug(
            f"A probe with the name `{name}` is already "
            "registered. Overwriting the entry with the new probe."
        )

    _probes[name] = probe


def unregister(name: str) -> None:
    if name in _probes:
        del _probes[name]
    if name in _probe_states:
        del _probe_states[name]
