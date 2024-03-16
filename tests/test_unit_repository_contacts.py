from datetime import datetime, timedelta
import os
import sys
from dotenv import load_dotenv
import unittest
from unittest.mock import MagicMock

from sqlalchemy.orm import Session


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv()


from src.database.models import User, Contact  # noqa: E402
from src.schemas import ContactModel  # noqa: E402
from src.repository.contacts import (  # noqa: E402
    get_contacts,
    get_contacts_birthdays,
    get_contact,
    create_contact,
    update_contact,
    remove_contact
)


class TestContactFunctions(unittest.IsolatedAsyncioTestCase):

    def setUp(self):

        self.fake_user = User(id=1, username='Test User')
        self.fake_contact = Contact(id=1, name='Test', last_name='User', email='test@example.com', user_id=self.fake_user.id)
        self.fake_db = MagicMock(spec=Session)

    async def test_get_contacts(self):

        self.fake_db.query(Contact).filter().all.return_value = [self.fake_contact]

        contacts = await get_contacts(self.fake_db, self.fake_user, name='Test')
        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0].name, 'Test')

        contacts = await get_contacts(self.fake_db, self.fake_user, last_name='User')
        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0].last_name, 'User')

        contacts = await get_contacts(self.fake_db, self.fake_user, email='test@example.com')
        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0].email, 'test@example.com')

    async def test_get_contacts_not_found(self):
        self.fake_db.query(Contact).filter().all.return_value = []
        contacts = await get_contacts(self.fake_db, self.fake_user, name='Nonexistent')
        self.assertEqual(len(contacts), 0)

    async def test_get_contacts_birthdays(self):
        today = datetime.now().date()
        contacts_with_birthdays = [
            Contact(id=i, name=f'Test{i}', last_name='User', email=f'test{i}@example.com', user_id=self.fake_user.id, born_date=today + timedelta(days=i))
            for i in range(1, 8)
        ]
        self.fake_db.query(Contact).filter().all.return_value = contacts_with_birthdays
        contacts = await get_contacts_birthdays(self.fake_db, self.fake_user)
        self.assertEqual(len(contacts), 7)
        for contact in contacts:
            self.assertLessEqual(abs((contact.born_date.replace(year=today.year) - today).days), 7)

    async def test_get_contacts_birthdays_not_found(self):
        self.fake_db.query(Contact).filter().all.return_value = []
        contacts = await get_contacts_birthdays(self.fake_db, self.fake_user)
        self.assertEqual(len(contacts), 0)

    async def test_get_contact(self):
        self.fake_db.query(Contact).filter().first.return_value = self.fake_contact
        contact = await get_contact(1, self.fake_db, self.fake_user)
        self.assertEqual(contact.name, 'Test')

    async def test_get_contact_not_found(self):
        self.fake_db.query(Contact).filter().first.return_value = None
        contact = await get_contact(1, self.fake_db, self.fake_user)
        self.assertIsNone(contact)

    async def test_create_contact(self):
        body = ContactModel(name='New', last_name='Contact', email='new@example.com', phone='0506789556', born_date=datetime(2000, 1, 1))
        contact = await create_contact(body, self.fake_db, self.fake_user)
        self.assertEqual(contact.name, 'New')

    async def test_update_contact(self):
        self.fake_db.query(Contact).filter().first.return_value = self.fake_contact
        body = ContactModel(name='Updated', last_name='Contact', email='updated@example.com', phone='0506789556', born_date=datetime(2000, 1, 1))
        contact = await update_contact(1, body, self.fake_db, self.fake_user)
        self.assertEqual(contact.name, 'Updated')

    async def test_update_contact_not_found(self):
        self.fake_db.query(Contact).filter().first.return_value = None
        body = ContactModel(name='Updated', last_name='Contact', email='updated@example.com', phone='0506789556', born_date=datetime(2000, 1, 1))
        contact = await update_contact(1, body, self.fake_db, self.fake_user)
        self.assertIsNone(contact)

    async def test_remove_contact(self):
        self.fake_db.query(Contact).filter().first.return_value = self.fake_contact
        contact = await remove_contact(1, self.fake_db, self.fake_user)
        self.assertEqual(contact.name, 'Test')

    async def test_remove_contact_not_found(self):
        self.fake_db.query(Contact).filter().first.return_value = None
        contact = await remove_contact(1, self.fake_db, self.fake_user)
        self.assertIsNone(contact)


if __name__ == '__main__':
    unittest.main()