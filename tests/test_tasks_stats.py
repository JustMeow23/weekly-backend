import uuid
from datetime import time, date, timedelta

from app.models import User, Task
from app.dao.tasks import TaskDAO


async def _make_user(session) -> User:
    user = User(
        id=uuid.uuid4(),
        email=f"{uuid.uuid4()}@test.com",
        password="x",
        fullName="Test",
    )
    session.add(user)
    await session.commit()
    return user


def _task(user_id, d, *, completed=False, postponed=0, type_="task") -> Task:
    return Task(
        id=uuid.uuid4(),
        date=d,
        title="t",
        timeFrom=time(10, 0),
        timeTo=time(11, 0),
        isCompleted=completed,
        isFavorite=False,
        type=type_,
        postponedCount=postponed,
        user_id=user_id,
    )


async def test_compute_stats_past_year_classification(session):
    user = await _make_user(session)
    session.add_all([
        _task(user.id, "2000-06-15", completed=True),
        _task(user.id, "2000-06-16"),
        _task(user.id, "2000-06-17", postponed=2),
        _task(user.id, "2000-06-18", type_="reminder"),
    ])
    await session.commit()

    stats = await TaskDAO.compute_stats(session, user.id, 2000)
    assert stats == {
        "year": 2000,
        "completed": 1,
        "missed": 2,
        "postponed": 0,
        "total": 3,
        "percent": 33,
    }


async def test_compute_stats_postponed_future(session):
    user = await _make_user(session)
    future = date.today() + timedelta(days=2)
    year = future.year
    session.add_all([
        _task(user.id, future.isoformat(), postponed=1),
        _task(user.id, future.isoformat(), postponed=0),
    ])
    await session.commit()

    stats = await TaskDAO.compute_stats(session, user.id, year)
    assert stats["completed"] == 0
    assert stats["missed"] == 0
    assert stats["postponed"] == 1
    assert stats["total"] == 1
    assert stats["percent"] == 0


async def test_compute_stats_empty(session):
    user = await _make_user(session)
    stats = await TaskDAO.compute_stats(session, user.id, 2024)
    assert stats == {
        "year": 2024, "completed": 0, "missed": 0,
        "postponed": 0, "total": 0, "percent": 0,
    }


async def test_postpone_increments_on_date_change(session):
    user = await _make_user(session)
    task = _task(user.id, "2024-01-01")
    session.add(task)
    await session.commit()

    updated = await TaskDAO.postpone(
        session, task.id, user.id, "2024-01-05", time(12, 0), time(13, 0)
    )
    assert updated.postponedCount == 1
    assert updated.date == "2024-01-05"
    assert updated.timeFrom == time(12, 0)


async def test_postpone_same_day_also_increments(session):
    user = await _make_user(session)
    task = _task(user.id, "2024-01-01")
    session.add(task)
    await session.commit()

    updated = await TaskDAO.postpone(
        session, task.id, user.id, "2024-01-01", time(11, 0), time(12, 0)
    )
    assert updated.postponedCount == 1
    assert updated.timeFrom == time(11, 0)


async def test_postpone_missing_returns_none(session):
    user = await _make_user(session)
    result = await TaskDAO.postpone(
        session, uuid.uuid4(), user.id, "2024-01-05", time(12, 0), time(13, 0)
    )
    assert result is None