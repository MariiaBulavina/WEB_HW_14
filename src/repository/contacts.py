from datetime import datetime, timedelta
from typing import List

from sqlalchemy import and_, or_, extract
from sqlalchemy.orm import Session

from src.database.models import Contact, User
from src.schemas import ContactModel


async def get_contacts(db: Session, user: User, name: str = None, last_name: str = None, email: str = None) -> List[Contact]:

    """
    The get_contacts function returns a list of contacts that match the given parameters.
    If no parameters are provided, it will return all contacts for the user.

    :param db: Session: Connection to the database
    :param user: User: User who owns the contacts
    :param name: str: Specifies the name by which contacts will be filtered
    :param last_name: str: Specifies the last name by which contacts will be filtered
    :param email: str: Specifies the email by which contacts will be filtered
    :return: A list of contacts
    """
    queries = []

    if name:
        queries.append(Contact.name == name)
    if last_name:
        queries.append(Contact.last_name == last_name)
    if email:
        queries.append(Contact.email == email)

    contacts = db.query(Contact).filter(and_(*queries, Contact.user_id == user.id)).all()
    return contacts


async def get_contacts_birthdays(db: Session, user: User) -> List[Contact]:

    """
    The get_contacts_birthdays function returns a list of contacts that have birthdays in the next 7 days.

    :param db: Session: Connection to the database
    :param user: User: User who owns the contacts
    :return: A list of contacts that have a birthday in the next 7 days
    """
    today = datetime.now().date()
    last_day = today + timedelta(days=7)

    dates = db.query(Contact).filter(or_
                                        (and_(extract('month', Contact.born_date) == last_day.month,
                                               extract('day', Contact.born_date) <= last_day.day,
                                               Contact.user_id == user.id),
                                               

                                        and_(extract('month', Contact.born_date) == today.month,
                                               extract('day', Contact.born_date) >= today.day,
                                               Contact.user_id == user.id))).all()

    return dates


async def get_contact(contact_id: int, db: Session, user: User) -> Contact:
    """
    The get_contact function takes in a contact_id and returns the corresponding Contact object.
   
    :param contact_id: int: Specifies the id of the contact we want to retrieve
    :param db: Session: Connection to the database
    :param user: User: User who owns the contact
    :return: The first contact with the given id
    """
    return db.query(Contact).filter(and_(Contact.id == contact_id, Contact.user_id == user.id)).first()


async def create_contact(body: ContactModel, db: Session, user: User) -> Contact:

    """
    The create_contact function creates a new contact in the database.

    :param body: ContactModel: Information to create a contact
    :param db: Session: Connection to the database
    :param user: User: The user to create the contact for
    :return: The contact object
    """
    contact = Contact(name = body.name, last_name = body.last_name, email = body.email, phone = body.phone, born_date = body.born_date, user = user)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


async def update_contact(contact_id: int, body: ContactModel, db: Session, user: User) -> Contact | None:

    """
    The update_contact function updates a contact in the database.
    
    :param contact_id: int: Specifies the id of the contact we want to update
    :param body: ContactModel: Information to update a contact
    :param db: Session: Connection to the database
    :param user: User: User who owns the contact
    :return: A contact object or none if the contact doesn't exist
    """
    contact = db.query(Contact).filter(and_(Contact.id == contact_id, Contact.user_id == user.id)).first()

    if contact:
        contact.name = body.name
        contact.last_name = body.last_name
        contact.email = body.email
        contact.phone = body.phone
        contact.born_date = body.born_date
        db.commit()
    return contact


async def remove_contact(contact_id: int, db: Session, user: User)  -> Contact | None:

    """
    The remove_contact function removes a contact from the database.
   
    :param contact_id: int: Specifies the id of the contact we want to retrieve
    :param db: Session: Connection to the database
    :param user: User: User who owns the contact
    :return: The contact that was removed
    """
    contact = db.query(Contact).filter(and_(Contact.id == contact_id, Contact.user_id == user.id)).first()
    
    if contact:
        db.delete(contact)
        db.commit()
    return contact
