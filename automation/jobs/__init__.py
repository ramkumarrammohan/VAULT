"""Job registry.

New automations (corporate actions, mutual-fund NAV, ...) only need to
subclass :class:`~automation.jobs.base.Job` and be added to ``_JOBS``.
"""

from .base import Job
from .bhavcopy_prices import BhavcopyPriceSyncJob

#: Registered job classes, keyed by their stable name.
_JOBS = {
    BhavcopyPriceSyncJob.name: BhavcopyPriceSyncJob,
}


def available_jobs() -> list:
    """Return metadata for every registered job."""
    return [
        {'name': name, 'description': job.description}
        for name, job in sorted(_JOBS.items())
    ]


def get_job(name: str) -> Job:
    """Instantiate a registered job by name."""
    try:
        return _JOBS[name]()
    except KeyError:
        known = ', '.join(sorted(_JOBS)) or 'none'
        raise KeyError(f"Unknown job '{name}'. Available: {known}") from None


def has_job(name: str) -> bool:
    return name in _JOBS


__all__ = ['Job', 'available_jobs', 'get_job', 'has_job']
