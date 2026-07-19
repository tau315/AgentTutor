from datetime import datetime, time

import pytest
from pydantic import ValidationError

from app.scheduling.schemas import AvailabilityReplace, AvailabilityWindowInput, BlockedTimeCreate
from app.sessions.schemas import SessionRequest, SessionReschedule


def test_weekly_window_requires_an_ordered_time_range():
    with pytest.raises(ValidationError):
        AvailabilityWindowInput(
            weekday=0,
            start_time=time(17, 0),
            end_time=time(9, 0),
            timezone="America/New_York",
        )


def test_session_request_requires_timezone_aware_datetimes():
    with pytest.raises(ValidationError):
        SessionRequest(
            tutor_id="tutor-1",
            subject="Calculus",
            starts_at=datetime(2026, 7, 20, 10, 0),
            ends_at=datetime(2026, 7, 20, 11, 0),
        )


def test_reschedule_rejects_an_end_before_the_start():
    with pytest.raises(ValidationError):
        SessionReschedule(
            starts_at="2026-07-20T11:00:00-04:00",
            ends_at="2026-07-20T10:00:00-04:00",
        )


def test_blocked_time_accepts_offsets_and_valid_order():
    block = BlockedTimeCreate(
        starts_at="2026-07-20T12:00:00-04:00",
        ends_at="2026-07-20T13:00:00-04:00",
        reason="Lunch",
    )

    assert block.starts_at.utcoffset() is not None


def test_weekly_windows_cannot_overlap():
    with pytest.raises(ValidationError):
        AvailabilityReplace(
            windows=[
                {"weekday": 0, "start_time": "09:00", "end_time": "12:00", "timezone": "America/New_York"},
                {"weekday": 0, "start_time": "11:00", "end_time": "13:00", "timezone": "America/New_York"},
            ]
        )
