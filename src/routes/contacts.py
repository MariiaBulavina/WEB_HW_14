from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.orm import Session

from src.database.models import User
from src.database.db import get_db
from src.schemas import ContactModel, ContactResponse
from src.repository import contacts as repository_contacts
from src.services.auth import auth_service


router = APIRouter(prefix='/contacts', tags=['contacts'])


@router.get('/', response_model=List[ContactResponse], description='No more than 2 requests per 5 seconds',
            dependencies=[Depends(RateLimiter(times=2, seconds=5))])
async def read_contacts(name: str = None, last_name: str = None, email: str = None, db: Session = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    
    """
    The read_contacts function returns a list of contacts.

    :param name: str: Specifies the name by which contacts will be filtered
    :param last_name: str: Specifies the last name by which contacts will be filtered
    :param email: str: Specifies the email by which contacts will be filtered
    :param db: Session: Connection to the database
    :param user: User: User who owns the contacts
    :return: A list of contacts
    """
    contacts = await repository_contacts.get_contacts(db, user, name, last_name, email)
    return contacts


@router.get('/birthdays', response_model=List[ContactResponse], description='No more than 2 requests per 5 seconds',
            dependencies=[Depends(RateLimiter(times=2, seconds=5))])
async def read_contacts_birthdays(db: Session = Depends(get_db), user: User = Depends(auth_service.get_current_user)):

    """
    The read_contacts_birthdays function returns a list of contacts with birthdays in the current month.

    :param db: Session: Connection to the database
    :param user: User: User who owns the contacts
    :return: A list of contacts with birthdays
    """
    contacts = await repository_contacts.get_contacts_birthdays(db, user)
    return contacts


@router.get('/{contact_id}', response_model=ContactResponse, description='No more than 2 requests per 5 seconds',
            dependencies=[Depends(RateLimiter(times=2, seconds=5))])
async def read_contact(contact_id: int, db: Session = Depends(get_db), user: User = Depends(auth_service.get_current_user)):

    """
    The read_contact function will return a contact by its id.

    :param contact_id: int: Specifies the id of the contact we want to retrieve
    :param db: Session: Connection to the database
    :param user: User: User who owns the contact
    :return: A contact object
    """
    contact = await repository_contacts.get_contact(contact_id, db, user)

    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact not found')
    return contact


@router.post('/', response_model=ContactResponse, status_code=status.HTTP_201_CREATED, description='No more than 2 requests per 5 seconds',
            dependencies=[Depends(RateLimiter(times=2, seconds=5))])
async def create_contact(body: ContactModel, db: Session = Depends(get_db), user: User = Depends(auth_service.get_current_user)):

    """
    The create_contact function creates a new contact in the database.

    :param body: ContactModel: Pass the contact data to the function
    :param db: Session: Connection to the database
    :param user: User: The user to create the contact for
    :return: A contact object
    """
    return await repository_contacts.create_contact(body, db, user)


@router.put('/{contact_id}', response_model=ContactResponse, description='No more than 2 requests per 5 seconds',
            dependencies=[Depends(RateLimiter(times=2, seconds=5))])
async def update_contact(body: ContactModel, contact_id: int, db: Session = Depends(get_db), user: User = Depends(auth_service.get_current_user)):

    """
    The update_contact function updates a contact in the database.

    :param body: ContactModel: Information to update a contact
    :param contact_id: int: Specifies the id of the contact we want to update
    :param db: Session: Connection to the database
    :param user: User: User who owns the contact
    :return: The updated contact
    """
    contact = await repository_contacts.update_contact(contact_id, body, db, user)

    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact not found')
    return contact


@router.delete('/{contact_id}', response_model=ContactResponse, description='No more than 2 requests per 5 seconds',
            dependencies=[Depends(RateLimiter(times=2, seconds=5))])
async def remove_contact(contact_id: int, db: Session = Depends(get_db), user: User = Depends(auth_service.get_current_user)):

    """
    The remove_contact function removes a contact from the database.

    :param contact_id: int: Specifies the id of the contact we want to remove
    :param db: Session: Connection to the database
    :param user: User: User who owns the contact
    :return: A contact object
    """
    contact = await repository_contacts.remove_contact(contact_id, db, user)

    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact not found')
    return contact
