import os
import sys
from dotenv import load_dotenv
import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session
from libgravatar import Gravatar


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv()


from src.database.models import User  # noqa: E402
from src.schemas import UserModel  # noqa: E402
from src.repository.users import (  # noqa: E402
    get_user_by_email,
    create_user,
    update_token,
    confirmed_email,
    update_avatar_url
)


class TestUserFunctions(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session = MagicMock(spec=Session)

    async def test_get_user_by_email(self):
        
        email = 'test@example.com'
        user = User(email=email)
        self.session.query(User).filter(User.email == email).first.return_value = user

        result = await get_user_by_email(email, self.session)
        self.assertEqual(result, user)

    async def test_create_user(self):
        
        body = UserModel(username='Test User', email='test@example.com', password='password')
        self.session.add.return_value = None
        self.session.commit.return_value = None
        self.session.refresh.return_value = None

        with patch.object(Gravatar, 'get_image', return_value='avatar_url'):
            result = await create_user(body, self.session)

        self.assertIsInstance(result, User)
        self.assertEqual(result.username, body.username)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.password, body.password)
        self.assertEqual(result.avatar, 'avatar_url')

    async def test_update_token(self):
        
        user = User(email='test@example.com')
        token = 'new_token'
        self.session.commit.return_value = None

        await update_token(user, token, self.session)
        self.assertEqual(user.refresh_token, token)

    async def test_confirmed_email(self):
        
        email = 'test@example.com'
        user = User(email=email, confirmed=False)
        self.session.query(User).filter(User.email == email).first.return_value = user
        self.session.commit.return_value = None

        await confirmed_email(email, self.session)
        self.assertTrue(user.confirmed)

    async def test_update_avatar_url(self):
        
        email = 'test@example.com'
        url = 'new_avatar_url'
        user = User(email=email, avatar='old_avatar_url')
        self.session.query(User).filter(User).first.return_value = user
        self.session.commit.return_value = None

        result = await update_avatar_url(email, url, self.session)
        self.assertEqual(result.avatar, url)

if __name__ == '__main__':
    unittest.main()