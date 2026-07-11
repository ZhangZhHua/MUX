import os
import json
from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from config.database import get_db
from models.event import LabEvent, EventComment, EventTag
from models.experiment import Experiment
from models.user import User, Group
from schemas.event import EventCreate, EventResponse, EventCommentCreate, EventCommentResponse, EventTagResponse
from routers.auth import get_current_user
from routers.experiment import log_telemetry_activity

router = APIRouter(prefix="/events", tags=["Events"])

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def get_occurrences_for_event(event: LabEvent, view_start: date, view_end: date) -> List[date]:
    start_date_val = event.start_date.date()
    end_date_val = event.recurrence_end_date.date() if event.recurrence_end_date else None
    
    # Parse exceptions
    exceptions = set()
    if event.exception_dates:
        try:
            exceptions = set(json.loads(event.exception_dates))
        except Exception:
            pass

    occurrences = []
    
    # If no recurrence
    if not event.recurrence_rule:
        if view_start <= start_date_val <= view_end:
            occurrences.append(start_date_val)
        return occurrences

    # Recurrence rules
    rule = event.recurrence_rule.lower()
    
    curr = view_start
    while curr <= view_end:
        # Check start date
        if curr < start_date_val:
            curr += timedelta(days=1)
            continue
            
        # Check end date
        if end_date_val and curr > end_date_val:
            curr += timedelta(days=1)
            continue
            
        # Check exceptions
        if curr.strftime("%Y-%m-%d") in exceptions:
            curr += timedelta(days=1)
            continue
            
        is_match = False
        if rule == "weekly":
            delta_days = (curr - start_date_val).days
            if delta_days % 7 == 0:
                is_match = True
        elif rule == "biweekly":
            delta_days = (curr - start_date_val).days
            if delta_days % 14 == 0:
                is_match = True
        elif rule == "monthly":
            if curr.day == start_date_val.day:
                is_match = True
            
        if is_match:
            occurrences.append(curr)
            
        curr += timedelta(days=1)
        
    return occurrences


# Helper: get the set of group IDs accessible by a user
def get_user_accessible_group_ids(user: User) -> set:
    if user.role == "sys_admin":
        return None  # None means all groups
    return {g.id for g in user.groups}


# 1. Fetch Events with optional group_id filtering
@router.get("", response_model=List[EventResponse])
def get_events(
    start_date: str = Query(..., description="Start date of the range in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date of the range in YYYY-MM-DD format"),
    group_id: Optional[int] = Query(None, description="Filter events by group. 0 = all user groups, omit for all accessible"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        view_start = datetime.strptime(start_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    
    if end_date:
        try:
            view_end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end date format. Use YYYY-MM-DD.")
    else:
        view_end = view_start + timedelta(days=6)
    
    # Determine which group IDs to include
    accessible_groups = get_user_accessible_group_ids(current_user)
    
    # Build the base query
    query = db.query(LabEvent)
    
    if accessible_groups is not None:
        # Non-sys_admin: only see events from their own groups
        if group_id is not None and group_id > 0:
            # Specific group selected — check user belongs to it
            if group_id not in accessible_groups:
                raise HTTPException(status_code=403, detail="You do not have access to this research group.")
            query = query.filter(LabEvent.group_id == group_id)
        else:
            # All My Teams or no filter specified — all user's groups
            query = query.filter(LabEvent.group_id.in_(accessible_groups))
    else:
        # sys_admin: see everything, optionally filter by specific group
        if group_id is not None and group_id > 0:
            query = query.filter(LabEvent.group_id == group_id)
    
    all_events = query.all()
    
    expanded_events = []
    
    for event in all_events:
        # Get occurrences
        occurrences = get_occurrences_for_event(event, view_start, view_end)
        
        # Resolve experiment title if exists
        exp_title = event.experiment.title if event.experiment else None
        
        for occ in occurrences:
            occ_str = occ.strftime("%Y-%m-%d")
            
            # Construct a response object
            resp = EventResponse.from_orm(event)
            resp.experiment_title = exp_title
            resp.instance_date = occ_str
            resp.unique_key = f"{event.id}_{occ_str}"
            
            # Shift start_date and end_date to the occurrence date for parent template events
            if event.recurrence_rule and not event.parent_event_id:
                orig_start = event.start_date
                resp.start_date = datetime.combine(occ, orig_start.time())
                if event.end_date:
                    duration = event.end_date - event.start_date
                    resp.end_date = resp.start_date + duration
                else:
                    resp.end_date = None
            
            expanded_events.append(resp)
            
    # Sort events by instance_date and then by created_at
    expanded_events.sort(key=lambda x: (x.instance_date, x.created_at))
    return expanded_events


# 2. Create Event
@router.post("", response_model=EventResponse)
def create_event(
    event_in: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate user belongs to the specified group
    if current_user.role != "sys_admin":
        user_group_ids = {g.id for g in current_user.groups}
        if event_in.group_id not in user_group_ids:
            raise HTTPException(
                status_code=403, 
                detail="You can only create events in groups you belong to."
            )
    
    # Verify the group exists
    group = db.query(Group).filter(Group.id == event_in.group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Research group not found.")
    
    # Resolve tags
    db_tags = []
    for tag_name in event_in.tags:
        cleaned_name = tag_name.strip()
        if not cleaned_name:
            continue
        tag = db.query(EventTag).filter(EventTag.name == cleaned_name).first()
        if not tag:
            tag = EventTag(name=cleaned_name)
            db.add(tag)
            db.commit()
            db.refresh(tag)
        db_tags.append(tag)
        
    # Resolve participants
    db_participants = []
    if event_in.participants:
        db_participants = db.query(User).filter(User.id.in_(event_in.participants)).all()
        
    db_event = LabEvent(
        title=event_in.title,
        description=event_in.description,
        experiment_id=event_in.experiment_id,
        author_id=current_user.id,
        group_id=event_in.group_id,
        start_date=event_in.start_date,
        end_date=event_in.end_date,
        is_important=event_in.is_important,
        recurrence_rule=event_in.recurrence_rule,
        recurrence_end_date=event_in.recurrence_end_date,
        tags=db_tags,
        participants=db_participants
    )
    
    db_event.attachments = event_in.attachments
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    # Audit telemetry
    log_telemetry_activity(
        db,
        user_id=current_user.id,
        action="created a schedule event",
        target=f"Event #{db_event.id}: {db_event.title}",
        group_id=event_in.group_id
    )
    
    return db_event


# 3. Update Event (Supports Series or Instance modifications)
@router.put("/{id}", response_model=EventResponse)
def update_event(
    id: int,
    event_in: EventCreate,
    instance_date: Optional[str] = Query(None, description="The specific date of the instance being modified, if any"),
    modify_series: bool = Query(True, description="Whether to modify the entire series or just this occurrence"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_event = db.query(LabEvent).filter(LabEvent.id == id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    # Check permissions (author or admin, and group membership)
    if db_event.author_id != current_user.id and current_user.role != "sys_admin":
        # team_admin can edit events in their own groups
        if current_user.role == "team_admin":
            user_group_ids = {g.id for g in current_user.groups}
            if db_event.group_id not in user_group_ids:
                raise HTTPException(status_code=403, detail="Permission denied. You can only edit events in your own groups.")
        else:
            raise HTTPException(status_code=403, detail="Permission denied. You can only edit your own events.")
    
    # Validate group_id change
    if current_user.role != "sys_admin":
        user_group_ids = {g.id for g in current_user.groups}
        if event_in.group_id not in user_group_ids:
            raise HTTPException(status_code=403, detail="You can only assign events to groups you belong to.")
    
    # Handle Tags
    db_tags = []
    for tag_name in event_in.tags:
        cleaned_name = tag_name.strip()
        if not cleaned_name:
            continue
        tag = db.query(EventTag).filter(EventTag.name == cleaned_name).first()
        if not tag:
            tag = EventTag(name=cleaned_name)
            db.add(tag)
            db.commit()
            db.refresh(tag)
        db_tags.append(tag)

    # Editing a single instance of a recurring event
    if db_event.recurrence_rule and not modify_series and instance_date:
        # 1. Add instance_date to parent event's exceptions
        exceptions = []
        if db_event.exception_dates:
            try:
                exceptions = json.loads(db_event.exception_dates)
            except Exception:
                pass
        if instance_date not in exceptions:
            exceptions.append(instance_date)
            db_event.exception_dates = json.dumps(exceptions)
            
        # 2. Create a new standalone override event
        override_date = datetime.strptime(instance_date, "%Y-%m-%d")
        # Keep time from event_in.start_date but set date to instance_date
        override_start = datetime.combine(override_date.date(), event_in.start_date.time())
        override_end = None
        if event_in.end_date:
            override_end = datetime.combine(override_date.date(), event_in.end_date.time())
        
        # Resolve participants for child
        db_participants = []
        if event_in.participants:
            db_participants = db.query(User).filter(User.id.in_(event_in.participants)).all()

        child_event = LabEvent(
            title=event_in.title,
            description=event_in.description,
            experiment_id=event_in.experiment_id,
            author_id=current_user.id,
            group_id=event_in.group_id,
            start_date=override_start,
            end_date=override_end,
            is_important=event_in.is_important,
            parent_event_id=db_event.id,
            tags=db_tags,
            participants=db_participants
        )
        child_event.attachments = event_in.attachments
        db.add(child_event)
        db.commit()
        db.refresh(child_event)
        
        log_telemetry_activity(
            db,
            user_id=current_user.id,
            action="modified event instance",
            target=f"Event #{child_event.id}: {child_event.title} (override)",
            group_id=event_in.group_id
        )
        
        return child_event
    else:
        # Update series or standalone event
        db_event.title = event_in.title
        db_event.description = event_in.description
        db_event.experiment_id = event_in.experiment_id
        db_event.group_id = event_in.group_id
        db_event.start_date = event_in.start_date
        db_event.end_date = event_in.end_date
        db_event.is_important = event_in.is_important
        db_event.attachments = event_in.attachments
        db_event.recurrence_rule = event_in.recurrence_rule
        db_event.recurrence_end_date = event_in.recurrence_end_date
        db_event.tags = db_tags
        
        # Update participants
        db_participants = []
        if event_in.participants:
            db_participants = db.query(User).filter(User.id.in_(event_in.participants)).all()
        db_event.participants = db_participants
        
        db.commit()
        db.refresh(db_event)
        
        log_telemetry_activity(
            db,
            user_id=current_user.id,
            action="modified event",
            target=f"Event #{db_event.id}: {db_event.title}",
            group_id=event_in.group_id
        )
        
        return db_event


# 4. Delete Event (series or instance)
@router.delete("/{id}")
def delete_event(
    id: int,
    delete_series: bool = Query(False, description="True to delete entire series, False for single occurrence"),
    instance_date: Optional[str] = Query(None, description="Specific date of the occurrence to delete"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_event = db.query(LabEvent).filter(LabEvent.id == id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    # Check permissions
    if db_event.author_id != current_user.id and current_user.role != "sys_admin":
        if current_user.role == "team_admin":
            user_group_ids = {g.id for g in current_user.groups}
            if db_event.group_id not in user_group_ids:
                raise HTTPException(status_code=403, detail="Permission denied.")
        else:
            raise HTTPException(status_code=403, detail="Permission denied.")
    
    group_id = db_event.group_id
    
    # If recurring event and not deleting the whole series, add exception
    if db_event.recurrence_rule and not delete_series and instance_date:
        exceptions = []
        if db_event.exception_dates:
            try:
                exceptions = json.loads(db_event.exception_dates)
            except Exception:
                pass
        if instance_date not in exceptions:
            exceptions.append(instance_date)
            db_event.exception_dates = json.dumps(exceptions)
            db.commit()
        
        log_telemetry_activity(
            db,
            user_id=current_user.id,
            action="deleted event occurrence",
            target=f"Event #{id} on {instance_date}",
            group_id=group_id
        )
        return
        
    else:
        # Delete series or standalone event
        # If it's a parent, cascade will delete all override events
        db.delete(db_event)
        db.commit()
        log_telemetry_activity(
            db,
            user_id=current_user.id,
            action="deleted event series",
            target=f"Event #{id}",
            group_id=group_id
        )
        return


# 🆕 5. Get Event Tags (Separate from experiment tags)
@router.get("/tags", response_model=List[EventTagResponse])
def get_event_tags(db: Session = Depends(get_db)):
    return db.query(EventTag).all()


# 6. Add Comment to Event
@router.post("/{id}/comments", response_model=EventCommentResponse)
def add_comment(
    id: int,
    comment_in: EventCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_event = db.query(LabEvent).filter(LabEvent.id == id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    # Check access by group membership
    accessible_groups = get_user_accessible_group_ids(current_user)
    if accessible_groups is not None and db_event.group_id not in accessible_groups:
        raise HTTPException(status_code=403, detail="You do not have access to this event.")
    
    db_comment = EventComment(
        event_id=db_event.id,
        author_id=current_user.id,
        content=comment_in.content
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


# 6. Fetch Comments for Event
@router.get("/{id}/comments", response_model=List[EventCommentResponse])
def get_comments(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_event = db.query(LabEvent).filter(LabEvent.id == id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    # Check access by group membership
    accessible_groups = get_user_accessible_group_ids(current_user)
    if accessible_groups is not None and db_event.group_id not in accessible_groups:
        raise HTTPException(status_code=403, detail="You do not have access to this event.")
    
    comments = db.query(EventComment).filter(EventComment.event_id == id).order_by(EventComment.created_at.asc()).all()
    return comments


# 7. Local File Upload for Event attachments
@router.post("/upload")
def upload_event_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    try:
        # Check size limit: 50MB
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Attachment size exceeds the maximum limit of 50MB"
            )

        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        return {"filename": file.filename, "url": f"/experiments/attachments/{file.filename}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File write error on lab server: {str(e)}")


# 8. Local file download/preview wrapper specifically for event files
from fastapi import Request
from fastapi.responses import FileResponse
from utils.security import decode_access_token

def get_current_user_from_header_or_query(
    request: Request,
    token: str = None,
    db: Session = Depends(get_db)
) -> Optional[User]:
    actual_token = token
    if not actual_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            actual_token = auth_header.split(" ")[1]
            
    if not actual_token:
        return None
        
    try:
        payload = decode_access_token(actual_token)
        if payload is None:
            return None
        email: str = payload.get("sub")
        if email is None:
            return None
        user = db.query(User).filter(User.email == email).first()
        return user
    except Exception:
        return None

@router.get("/attachments/{filename}")
def download_event_file(
    filename: str,
    request: Request,
    preview: bool = False,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    current_user = get_current_user_from_header_or_query(request, token, db)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing or invalid. Access denied."
        )
        
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    if preview:
        import mimetypes
        media_type, _ = mimetypes.guess_type(file_path)
        if not media_type:
            if filename.lower().endswith('.pdf'):
                media_type = "application/pdf"
            else:
                media_type = "application/octet-stream"
        return FileResponse(
            file_path,
            media_type=media_type,
            headers={"Content-Disposition": "inline"}
        )
    return FileResponse(file_path, filename=filename)
