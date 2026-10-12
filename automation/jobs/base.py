"""Base class for automation jobs."""

from abc import ABC, abstractmethod


class Job(ABC):
    """A unit of automation work.

    Jobs are instantiated with no arguments by the registry, so any
    configurable state must come from :mod:`automation.config` or be passed to
    :meth:`run` (which also makes them easy to test).
    """

    #: Stable identifier used in URLs / CLI (e.g. "bhavcopy").
    name: str = 'job'

    #: Human-readable summary.
    description: str = ''

    @abstractmethod
    def run(self, **kwargs) -> dict:
        """Execute the job and return a JSON-serialisable report."""
        raise NotImplementedError
