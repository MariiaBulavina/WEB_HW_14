from datetime import datetime, timedelta
import pickle
from typing import Optional

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
import redis
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.repository import users as repository_users
from src.conf.config import settings


class Auth:

    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    SECRET_KEY = settings.secret_key_jwt
    ALGORITHM = settings.algorithm
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login')
    cache = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0)

    def verify_password(self, plain_password, hashed_password):
        """
        The verify_password function takes a plain-text password and hashed
        password as arguments. It then uses the pwd_context object to verify that the
        plain-text password matches the hashed one.

        :param self: The instance of the class
        :param plain_password: The password that is entered by the user
        :param hashed_password: The hashed password
        :return: A boolean
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """
        The get_password_hash function takes a password as input and returns the hash of that password.
        The hash is generated using the pwd_context object, which is an instance of Flask-Bcrypt's Bcrypt class.

        :param self: The instance of the class
        :param password: str: The password that is to be hashed
        :return: The password hash
        """
        return self.pwd_context.hash(password)

    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        The create_access_token function creates a new access token.
            
        :param self: The instance of the class
        :param data: dict: The data that will be encoded into the jwt
        :param expires_delta: Optional[float]: The expiration time of the access token
        :return: A token that is encoded with the data,
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)

        to_encode.update({'iat': datetime.utcnow(), 'exp': expire, 'scope': 'access_token'})
        encoded_access_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_access_token

    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        The create_refresh_token function creates a refresh token for the user.
            
        :param self: The instance of the class
        :param data: dict: The user's information to be encoded into the token
        :param expires_delta: Optional[float]: The expiration time of the refresh token
        :return: A refresh token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=7)

        to_encode.update({'iat': datetime.utcnow(), 'exp': expire, 'scope': 'refresh_token'})
        encoded_refresh_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_refresh_token

    async def decode_refresh_token(self, refresh_token: str):
        """
        The decode_refresh_token function is used to decode the refresh token.
            It takes in a refresh_token as an argument and returns the email of the user if successful.
            If it fails, it raises an HTTPException with status code 401 (Unauthorized) and detail message 'Could not validate credentials'.

        :param self: The instance of the class
        :param refresh_token: str: Refresh token 
        :return: The email address of the user
        """
        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])

            if payload['scope'] == 'refresh_token':
                email = payload['sub']
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid scope for token')
        
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    #    """
    #     The get_current_user function is a dependency that will be used in the
    #         protected endpoints. It takes a token as an argument and returns the user
    #         object if it exists, otherwise it raises an exception.

    #     :param self: The instance of the class
    #     :param token: str: Token from the request header
    #     :param db: Connection to the database
    #     :return: The user object
    #     """
        credentials_exception = HTTPException(  
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )

        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])

            if payload['scope'] == 'access_token':
                email = payload['sub']
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
            
        except JWTError:
            raise credentials_exception

        user_hash = str(email)
        user = self.cache.get(user_hash)

        if user is None:
            
            user = await repository_users.get_user_by_email(email, db)

            if user is None:
                raise credentials_exception
            
            self.cache.set(user_hash, pickle.dumps(user))
            self.cache.expire(user_hash, 300)
        else:
            user = pickle.loads(user)
            
        return user

    def create_email_token(self, data: dict):

        """
        The create_email_token function takes in a dictionary of data and returns an encoded token.
        The function first creates a copy of the data dictionary, then adds two keys to it: iat (issued at) and exp (expiration).
        It then encodes the new dictionary using jwt.encode().

        :param self: The instance of the class
        :param data: dict: Data that will be encoded
        :return: A token that is encoded with the data passed in and a secret key
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({'iat': datetime.utcnow(), 'exp': expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    async def get_email_from_token(self, token: str):

        """
        The get_email_from_token function takes a token as an argument and returns the email address associated with that token.
        The function uses the jwt library to decode the token, which is then used to return the email address.

        :param self: The instance of the class
        :param token: str: Token that is sent to the user's email
        :return: The email address of the user that is associated with the token
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload['sub']
            return email
        
        except JWTError as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail='Invalid token for email verification')


auth_service = Auth()
