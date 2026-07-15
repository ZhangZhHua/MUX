"""Central, query-scoped authorization helpers.

Never load a tenant resource by id and authorize it afterwards: doing so makes
future callers very likely to forget the second check.  These helpers always
apply the group scope in the same database query as the resource id.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.experiment import Experiment
from models.daily_log import DailyLog
from models.user import Group, User, group_users_association


def accessible_group_ids(db: Session, user: User):
    if user.role == "sys_admin":
        return None
    return db.query(group_users_association.c.group_id).filter(
        group_users_association.c.user_id == user.id
    )


def require_group_member(db: Session, user: User, group_id: int) -> Group:
    query = db.query(Group).filter(Group.id == group_id)
    if user.role != "sys_admin":
        query = query.join(
            group_users_association,
            group_users_association.c.group_id == Group.id,
        ).filter(group_users_association.c.user_id == user.id)
    group = query.first()
    if not group:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this research group.")
    return group


def require_group_admin(db: Session, user: User, group_id: int) -> Group:
    group = require_group_member(db, user, group_id)
    if user.role not in {"sys_admin", "team_admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Group administrator privileges are required.")
    return group


def require_experiment_access(db: Session, user: User, experiment_id: int, *, include_deleted: bool = False) -> Experiment:
    query = db.query(Experiment).filter(Experiment.id == experiment_id)
    if not include_deleted:
        query = query.filter(Experiment.is_deleted.is_(False))
    if user.role != "sys_admin":
        query = query.join(
            group_users_association,
            group_users_association.c.group_id == Experiment.group_id,
        ).filter(group_users_association.c.user_id == user.id)
    experiment = query.first()
    if not experiment:
        # Deliberately do not disclose whether an inaccessible id exists.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found.")
    return experiment


def require_experiment_admin(db: Session, user: User, experiment_id: int, *, include_deleted: bool = False) -> Experiment:
    experiment = require_experiment_access(db, user, experiment_id, include_deleted=include_deleted)
    require_group_admin(db, user, experiment.group_id)
    return experiment


def require_daily_log_access(db: Session, user: User, log_id: int) -> DailyLog:
    query = db.query(DailyLog).join(Experiment, DailyLog.experiment_id == Experiment.id).filter(
        DailyLog.id == log_id,
        Experiment.is_deleted.is_(False),
    )
    if user.role != "sys_admin":
        query = query.join(
            group_users_association,
            group_users_association.c.group_id == Experiment.group_id,
        ).filter(group_users_association.c.user_id == user.id)
    log = query.first()
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log record not found.")
    return log
