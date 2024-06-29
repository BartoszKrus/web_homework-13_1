from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query, status

from sqlalchemy.orm import Session

from src.database.db import get_db
from src.schemas import ContactResponse, ContactCreate, ContactUpdate
from src.repository import contacts
from src.services.auth import auth_service
from src.database.models import User, Contact

from fastapi_limiter.depends import RateLimiter


router = APIRouter(prefix='/contacts', tags=["contacts"])


@router.post("/create", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(contact: ContactCreate, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    existing_contact = db.query(Contact).filter(Contact.email == contact.email, Contact.owner_id == current_user.id).first()
    if existing_contact:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contact with this email already exists."
        )
    return await contacts.create_contact(contact, current_user, db)

@router.get("/read_contacts", response_model=List[ContactResponse], description="No more than 10 requests per minute", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def read_contacts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    return await contacts.get_contacts(skip, limit, current_user, db)

@router.get("/read_contact/{contact_id}", response_model=ContactResponse)
async def read_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    db_contact = await contacts.get_contact(contact_id, current_user, db)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@router.put("/update_contact/{contact_id}", response_model=ContactResponse)
async def update_contact(contact_id: int, body: ContactUpdate, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    db_contact = await contacts.update_contact(contact_id, body, current_user, db)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@router.delete("/delete_contact/{contact_id}", response_model=ContactResponse)
async def delete_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    db_contact = await contacts.remove_contact(contact_id, current_user, db)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@router.get("/search", response_model=List[ContactResponse])
async def search_contacts(first_name: Optional[str] = Query(None), last_name: Optional[str] = Query(None), email: Optional[str] = Query(None), db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    db_contacts = await contacts.search_contact(first_name, last_name, email, current_user, db)
    if db_contacts is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contacts

@router.get("/birthdays", response_model=List[ContactResponse])
async def get_upcoming_birthdays(db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    db_contacts = await contacts.get_upcoming_birthdays(current_user, db)
    if db_contacts is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contacts







