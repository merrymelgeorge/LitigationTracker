"""
Litigation Tracker - Main Application
A web-based platform for tracking litigations
"""
import os
import shutil
from contextlib import asynccontextmanager
from datetime import datetime, date, timedelta
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from pydantic import BaseModel, EmailStr

from models import (
    init_db, get_db, User, Case, Party, Document, Hearing,
    Forum, CaseStatus, AffidavitStatus, UserRole
)
from auth import (
    get_password_hash, authenticate_user, create_access_token,
    get_current_user, get_current_user_optional, require_admin,
    create_default_admin, ACCESS_TOKEN_EXPIRE_MINUTES
)


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and create default admin on startup"""
    init_db()
    db = next(get_db())
    create_default_admin(db)
    db.close()
    yield
    # Cleanup on shutdown (if needed)


# Initialize app
app = FastAPI(title="Litigation Tracker", version="1.0.0", lifespan=lifespan)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

# Ensure upload directory exists
os.makedirs("uploads", exist_ok=True)


# ============== Pydantic Schemas ==============

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: str = "user"


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class PartyData(BaseModel):
    party_type: str
    party_number: int
    name: str
    address: Optional[str] = None


class HearingData(BaseModel):
    hearing_date: date
    brief: str


# ============== Helper Functions ==============

def generate_case_id(db: Session) -> str:
    """Generate case ID in YYYY001 format"""
    year = datetime.now().year
    prefix = str(year)
    
    # Find the highest case number for this year
    last_case = db.query(Case).filter(
        Case.case_id.like(f"{prefix}%")
    ).order_by(Case.case_id.desc()).first()
    
    if last_case:
        last_num = int(last_case.case_id[4:])
        new_num = last_num + 1
    else:
        new_num = 1
    
    return f"{prefix}{new_num:03d}"


def save_upload_file(upload_file: UploadFile, case_id: str, doc_type: str) -> str:
    """Save uploaded file and return path"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = os.path.splitext(upload_file.filename)[1]
    filename = f"{case_id}_{doc_type}_{timestamp}{ext}"
    filepath = os.path.join("uploads", filename)
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    return filepath


# ============== Auth Routes ==============

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, user: Optional[User] = Depends(get_current_user_optional)):
    """Redirect to dashboard or login"""
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle login"""
    user = authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid username or password"
        })
    
    access_token = create_access_token(data={"sub": user.username})
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    return response


@app.get("/logout")
async def logout():
    """Handle logout"""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response


# ============== Dashboard Routes ==============

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Main dashboard"""
    # Get statistics
    total_cases = db.query(Case).count()
    
    # Status-wise counts
    status_counts = db.query(Case.case_status, func.count(Case.id)).group_by(Case.case_status).all()
    status_stats = {status: count for status, count in status_counts}
    
    # Forum-wise counts
    forum_counts = db.query(Case.forum, func.count(Case.id)).group_by(Case.forum).all()
    forum_stats = {forum: count for forum, count in forum_counts}
    
    # Cases with hearing in next 10 days
    today = date.today()
    next_10_days = today + timedelta(days=10)
    upcoming_hearings = db.query(Case).filter(
        Case.next_hearing_date >= today,
        Case.next_hearing_date <= next_10_days
    ).order_by(Case.next_hearing_date).all()
    
    # Recent cases
    recent_cases = db.query(Case).order_by(Case.updated_at.desc()).limit(5).all()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "total_cases": total_cases,
        "status_stats": status_stats,
        "forum_stats": forum_stats,
        "upcoming_hearings": upcoming_hearings,
        "recent_cases": recent_cases,
        "statuses": [s.value for s in CaseStatus],
        "forums": [f.value for f in Forum]
    })


# ============== Case Routes ==============

@app.get("/cases", response_class=HTMLResponse)
async def list_cases(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    search: Optional[str] = None,
    status: Optional[str] = None,
    forum: Optional[str] = None,
    page: int = 1
):
    """List all cases with search and filters"""
    per_page = 20
    query = db.query(Case)
    
    # Apply filters
    if search:
        search_term = f"%{search}%"
        # Search in case number and party names
        party_case_ids = db.query(Party.case_id).filter(Party.name.ilike(search_term)).subquery()
        query = query.filter(or_(
            Case.case_no.ilike(search_term),
            Case.case_id.ilike(search_term),
            Case.id.in_(party_case_ids)
        ))
    
    if status:
        query = query.filter(Case.case_status == status)
    
    if forum:
        query = query.filter(Case.forum == forum)
    
    total = query.count()
    cases = query.order_by(Case.updated_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    total_pages = (total + per_page - 1) // per_page
    
    return templates.TemplateResponse("cases.html", {
        "request": request,
        "user": user,
        "cases": cases,
        "search": search or "",
        "current_status": status or "",
        "current_forum": forum or "",
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "statuses": [s.value for s in CaseStatus],
        "forums": [f.value for f in Forum]
    })


@app.get("/cases/new", response_class=HTMLResponse)
async def new_case_form(
    request: Request,
    user: User = Depends(get_current_user)
):
    """New case form"""
    return templates.TemplateResponse("case_form.html", {
        "request": request,
        "user": user,
        "case": None,
        "forums": [f.value for f in Forum],
        "statuses": [s.value for s in CaseStatus],
        "affidavit_statuses": [a.value for a in AffidavitStatus]
    })


@app.post("/cases/new")
async def create_case(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    forum: str = Form(...),
    case_type: str = Form(None),
    case_no: str = Form(None),
    connected_case_nos: str = Form(None),
    is_appeal: bool = Form(False),
    lower_court_case_no: str = Form(None),
    lower_court: str = Form(None),
    lower_court_order_date: str = Form(None),
    counsel_name: str = Form(None),
    counsel_contact: str = Form(None),
    asg_engaged: bool = Form(False),
    brief_facts: str = Form(None),
    last_hearing_date: str = Form(None),
    next_hearing_date: str = Form(None),
    affidavit_status: str = Form(None),
    case_status: str = Form(CaseStatus.FILED.value),
    lower_court_order_doc: UploadFile = File(None)
):
    """Create new case"""
    case_id = generate_case_id(db)
    
    # Parse dates
    lc_order_date = datetime.strptime(lower_court_order_date, "%Y-%m-%d").date() if lower_court_order_date else None
    last_hearing = datetime.strptime(last_hearing_date, "%Y-%m-%d").date() if last_hearing_date else None
    next_hearing = datetime.strptime(next_hearing_date, "%Y-%m-%d").date() if next_hearing_date else None
    
    # Handle file upload
    lc_order_doc_path = None
    if lower_court_order_doc and lower_court_order_doc.filename:
        lc_order_doc_path = save_upload_file(lower_court_order_doc, case_id, "lower_court_order")
    
    case = Case(
        case_id=case_id,
        forum=forum,
        case_type=case_type,
        case_no=case_no,
        connected_case_nos=connected_case_nos,
        is_appeal=is_appeal,
        lower_court_case_no=lower_court_case_no,
        lower_court=lower_court,
        lower_court_order_date=lc_order_date,
        lower_court_order_doc=lc_order_doc_path,
        counsel_name=counsel_name,
        counsel_contact=counsel_contact,
        asg_engaged=asg_engaged,
        brief_facts=brief_facts,
        last_hearing_date=last_hearing,
        next_hearing_date=next_hearing,
        affidavit_status=affidavit_status,
        case_status=case_status,
        created_by=user.id,
        updated_by=user.id
    )
    
    db.add(case)
    db.commit()
    db.refresh(case)
    
    return RedirectResponse(url=f"/cases/{case.id}", status_code=302)


@app.get("/cases/{case_id}", response_class=HTMLResponse)
async def view_case(
    request: Request,
    case_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """View case details"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    petitioners = db.query(Party).filter(Party.case_id == case_id, Party.party_type == "petitioner").order_by(Party.party_number).all()
    respondents = db.query(Party).filter(Party.case_id == case_id, Party.party_type == "respondent").order_by(Party.party_number).all()
    documents = db.query(Document).filter(Document.case_id == case_id).order_by(Document.filing_date.desc()).all()
    hearings = db.query(Hearing).filter(Hearing.case_id == case_id).order_by(Hearing.hearing_date.desc()).all()
    
    return templates.TemplateResponse("case_view.html", {
        "request": request,
        "user": user,
        "case": case,
        "petitioners": petitioners,
        "respondents": respondents,
        "documents": documents,
        "hearings": hearings
    })


@app.get("/cases/{case_id}/edit", response_class=HTMLResponse)
async def edit_case_form(
    request: Request,
    case_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Edit case form"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    return templates.TemplateResponse("case_form.html", {
        "request": request,
        "user": user,
        "case": case,
        "forums": [f.value for f in Forum],
        "statuses": [s.value for s in CaseStatus],
        "affidavit_statuses": [a.value for a in AffidavitStatus]
    })


@app.post("/cases/{case_id}/edit")
async def update_case(
    request: Request,
    case_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    forum: str = Form(...),
    case_type: str = Form(None),
    case_no: str = Form(None),
    connected_case_nos: str = Form(None),
    is_appeal: bool = Form(False),
    lower_court_case_no: str = Form(None),
    lower_court: str = Form(None),
    lower_court_order_date: str = Form(None),
    counsel_name: str = Form(None),
    counsel_contact: str = Form(None),
    asg_engaged: bool = Form(False),
    brief_facts: str = Form(None),
    last_hearing_date: str = Form(None),
    next_hearing_date: str = Form(None),
    affidavit_status: str = Form(None),
    case_status: str = Form(CaseStatus.FILED.value),
    final_order_date: str = Form(None),
    lower_court_order_doc: UploadFile = File(None),
    final_order_doc: UploadFile = File(None)
):
    """Update case"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Update fields
    case.forum = forum
    case.case_type = case_type
    case.case_no = case_no
    case.connected_case_nos = connected_case_nos
    case.is_appeal = is_appeal
    case.lower_court_case_no = lower_court_case_no
    case.lower_court = lower_court
    case.lower_court_order_date = datetime.strptime(lower_court_order_date, "%Y-%m-%d").date() if lower_court_order_date else None
    case.counsel_name = counsel_name
    case.counsel_contact = counsel_contact
    case.asg_engaged = asg_engaged
    case.brief_facts = brief_facts
    case.last_hearing_date = datetime.strptime(last_hearing_date, "%Y-%m-%d").date() if last_hearing_date else None
    case.next_hearing_date = datetime.strptime(next_hearing_date, "%Y-%m-%d").date() if next_hearing_date else None
    case.affidavit_status = affidavit_status
    case.case_status = case_status
    case.final_order_date = datetime.strptime(final_order_date, "%Y-%m-%d").date() if final_order_date else None
    case.updated_by = user.id
    
    # Handle file uploads
    if lower_court_order_doc and lower_court_order_doc.filename:
        case.lower_court_order_doc = save_upload_file(lower_court_order_doc, case.case_id, "lower_court_order")
    
    if final_order_doc and final_order_doc.filename:
        case.final_order_doc = save_upload_file(final_order_doc, case.case_id, "final_order")
    
    db.commit()
    
    return RedirectResponse(url=f"/cases/{case_id}", status_code=302)


# ============== Party Routes ==============

@app.post("/cases/{case_id}/parties")
async def add_party(
    case_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    party_type: str = Form(...),
    name: str = Form(...),
    address: str = Form(None)
):
    """Add party to case"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Get next party number
    last_party = db.query(Party).filter(
        Party.case_id == case_id,
        Party.party_type == party_type
    ).order_by(Party.party_number.desc()).first()
    
    party_number = (last_party.party_number + 1) if last_party else 1
    
    party = Party(
        case_id=case_id,
        party_type=party_type,
        party_number=party_number,
        name=name,
        address=address
    )
    
    db.add(party)
    case.updated_by = user.id
    db.commit()
    
    return RedirectResponse(url=f"/cases/{case_id}", status_code=302)


@app.post("/parties/{party_id}/delete")
async def delete_party(
    party_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete party"""
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    
    case_id = party.case_id
    db.delete(party)
    
    case = db.query(Case).filter(Case.id == case_id).first()
    if case:
        case.updated_by = user.id
    
    db.commit()
    
    return RedirectResponse(url=f"/cases/{case_id}", status_code=302)


# ============== Document Routes ==============

@app.post("/cases/{case_id}/documents")
async def upload_document(
    case_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    doc_type: str = Form(...),
    filing_date: str = Form(None),
    file: UploadFile = File(...)
):
    """Upload document to case"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    filepath = save_upload_file(file, case.case_id, doc_type.replace(" ", "_"))
    
    document = Document(
        case_id=case_id,
        doc_type=doc_type,
        doc_name=file.filename,
        file_path=filepath,
        filing_date=datetime.strptime(filing_date, "%Y-%m-%d").date() if filing_date else None,
        uploaded_by=user.id
    )
    
    db.add(document)
    case.updated_by = user.id
    db.commit()
    
    return RedirectResponse(url=f"/cases/{case_id}", status_code=302)


@app.get("/documents/{doc_id}/download")
async def download_document(
    doc_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download document"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(doc.file_path, filename=doc.doc_name)


@app.post("/documents/{doc_id}/delete")
async def delete_document(
    doc_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete document"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    case_id = doc.case_id
    
    # Delete file
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    
    db.delete(doc)
    
    case = db.query(Case).filter(Case.id == case_id).first()
    if case:
        case.updated_by = user.id
    
    db.commit()
    
    return RedirectResponse(url=f"/cases/{case_id}", status_code=302)


# ============== Hearing Routes ==============

@app.post("/cases/{case_id}/hearings")
async def add_hearing(
    case_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    hearing_date: str = Form(...),
    brief: str = Form(...)
):
    """Add hearing to case"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    hearing = Hearing(
        case_id=case_id,
        hearing_date=datetime.strptime(hearing_date, "%Y-%m-%d").date(),
        brief=brief,
        created_by=user.id
    )
    
    db.add(hearing)
    
    # Update last hearing date
    case.last_hearing_date = hearing.hearing_date
    case.updated_by = user.id
    
    db.commit()
    
    return RedirectResponse(url=f"/cases/{case_id}", status_code=302)


@app.post("/hearings/{hearing_id}/delete")
async def delete_hearing(
    hearing_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete hearing"""
    hearing = db.query(Hearing).filter(Hearing.id == hearing_id).first()
    if not hearing:
        raise HTTPException(status_code=404, detail="Hearing not found")
    
    case_id = hearing.case_id
    db.delete(hearing)
    
    case = db.query(Case).filter(Case.id == case_id).first()
    if case:
        case.updated_by = user.id
    
    db.commit()
    
    return RedirectResponse(url=f"/cases/{case_id}", status_code=302)


# ============== User Management Routes ==============

@app.get("/users", response_class=HTMLResponse)
async def list_users(
    request: Request,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    users = db.query(User).order_by(User.created_at.desc()).all()
    user_count = db.query(User).filter(User.is_active == True).count()
    
    return templates.TemplateResponse("users.html", {
        "request": request,
        "user": user,
        "users": users,
        "user_count": user_count,
        "max_users": 10
    })


@app.post("/users")
async def create_user(
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    role: str = Form("user")
):
    """Create new user (admin only)"""
    # Check user limit
    active_users = db.query(User).filter(User.is_active == True).count()
    if active_users >= 10:
        raise HTTPException(status_code=400, detail="Maximum user limit (10) reached")
    
    # Check for existing username/email
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        role=role
    )
    
    db.add(user)
    db.commit()
    
    return RedirectResponse(url="/users", status_code=302)


@app.post("/users/{user_id}/toggle")
async def toggle_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Toggle user active status"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    
    user.is_active = not user.is_active
    db.commit()
    
    return RedirectResponse(url="/users", status_code=302)


@app.post("/users/{user_id}/delete")
async def delete_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    db.delete(user)
    db.commit()
    
    return RedirectResponse(url="/users", status_code=302)


@app.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    user: User = Depends(get_current_user)
):
    """User profile page for changing password"""
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user
    })


@app.post("/profile/change-password")
async def change_password(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...)
):
    """Change user's own password"""
    from auth import verify_password
    
    # Verify current password
    if not verify_password(current_password, user.hashed_password):
        return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": user,
            "error": "Current password is incorrect"
        })
    
    # Check new password confirmation
    if new_password != confirm_password:
        return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": user,
            "error": "New passwords do not match"
        })
    
    # Check password length
    if len(new_password) < 6:
        return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": user,
            "error": "Password must be at least 6 characters"
        })
    
    # Update password
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user,
        "success": "Password changed successfully!"
    })


@app.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
    new_password: str = Form(...)
):
    """Reset another user's password (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    return RedirectResponse(url="/users", status_code=302)


# ============== Excel Import Routes ==============

@app.get("/import", response_class=HTMLResponse)
async def import_page(
    request: Request,
    user: User = Depends(get_current_user),
    success: Optional[int] = None,
    errors: Optional[int] = None,
    message: Optional[str] = None
):
    """Excel import page"""
    return templates.TemplateResponse("import.html", {
        "request": request,
        "user": user,
        "success": success,
        "errors": errors,
        "message": message
    })


@app.post("/import")
async def import_excel(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    strict_mode: bool = Form(True)
):
    """Handle Excel file import"""
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        return templates.TemplateResponse("import.html", {
            "request": request,
            "user": user,
            "error": "Please upload an Excel file (.xlsx or .xls)"
        })
    
    try:
        # Import the excel processing module
        from excel_import import process_excel_file
        
        # Read file content
        content = await file.read()
        
        # Process the Excel file with strict mode setting
        success_count, error_count, error_messages = process_excel_file(
            content, db, user.id, strict_mode=strict_mode
        )
        
        return templates.TemplateResponse("import.html", {
            "request": request,
            "user": user,
            "success": success_count,
            "errors": error_count,
            "error_messages": error_messages[:20] if error_messages else [],  # Show first 20 errors
            "total_errors": len(error_messages) if error_messages else 0,
            "strict_mode": strict_mode
        })
        
    except Exception as e:
        return templates.TemplateResponse("import.html", {
            "request": request,
            "user": user,
            "error": f"Failed to process file: {str(e)}"
        })


@app.get("/import/template")
async def download_template(user: User = Depends(get_current_user)):
    """Download sample Excel template"""
    from excel_import import get_sample_template
    from io import BytesIO
    
    # Generate template
    df = get_sample_template()
    
    # Write to bytes
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    
    # Return as downloadable file
    from fastapi.responses import StreamingResponse
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=litigation_tracker_template.xlsx"}
    )


# ============== API Endpoints for Dashboard Charts ==============

@app.get("/api/stats")
async def get_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics"""
    status_counts = db.query(Case.case_status, func.count(Case.id)).group_by(Case.case_status).all()
    forum_counts = db.query(Case.forum, func.count(Case.id)).group_by(Case.forum).all()
    
    return {
        "status": {status: count for status, count in status_counts},
        "forum": {forum: count for forum, count in forum_counts}
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

