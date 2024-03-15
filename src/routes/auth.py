from fastapi import APIRouter, HTTPException, Depends, status, Security, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.schemas import UserModel, UserResponse, TokenModel, RequestEmail
from src.services.email import send_email


router = APIRouter(prefix='/auth', tags=['auth'])
security = HTTPBearer()


@router.post('/signup', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserModel, bt: BackgroundTasks, request: Request, db: Session = Depends(get_db)):

    """
    The signup function creates a new user in the database.
    It takes in a UserModel object, which is validated by pydantic.
    The password is hashed using Argon2 and stored as such.

    :param body: UserModel: Information to create a user
    :param bt: BackgroundTasks: Background task to run
    :param request: Request: The base url of the request
    :param db: Session: Connection to the database
    :return: A dictionary with the user and a detail message
    """
    exist_user = await repository_users.get_user_by_email(body.email, db)

    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Account already exists')
    
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    bt.add_task(send_email, new_user.email, new_user.username, str(request.base_url))

    return {'user': new_user, 'detail': 'User successfully created'}


@router.post('/login', response_model=TokenModel)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    """
    The login function is used to authenticate a user.

    :param body: OAuth2PasswordRequestForm: The username and password 
    :param db: Session: Connection to the database
    :return: A dictionary with the access_token, refresh_token and token type
    """
    user = await repository_users.get_user_by_email(body.username, db)

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid email')
    
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Email is not confirmed')
    
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid password')
    
    access_token = await auth_service.create_access_token(data={'sub': user.email})
    refresh_token = await auth_service.create_refresh_token(data={'sub': user.email})
    await repository_users.update_token(user, refresh_token, db)
    return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'bearer'}
   

@router.get('/refresh_token', response_model=TokenModel)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):

    """
    The refresh_token function is used to refresh the access token.
    The function takes in a refresh token and returns an access token, a new refresh token, and the type of authorization.

    :param credentials: HTTPAuthorizationCredentials: HTTP authorization credentials that contain a refresh token
    :param db: Session: Connection to the database
    :return: A new access_token and refresh_token for the user
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid refresh token')

    access_token = await auth_service.create_access_token(data={'sub': email})
    refresh_token = await auth_service.create_refresh_token(data={'sub': email})
    await repository_users.update_token(user, refresh_token, db)
    return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'bearer'}
    

@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: Session = Depends(get_db)):

    """
    The confirmed_email function is used to confirm a user's email address.

    :param token: str: Confirmation token
    :param db: Session: Connection to the database
    :return: A message if the email is already confirmed or confirms the email
    """
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)

    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Verification error')
    
    if user.confirmed:
        return {'message': 'Your email is already confirmed'}
    
    await repository_users.confirmed_email(email, db)
    return {'message': 'Email confirmed'}


@router.post('/request_email')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)):

    """
    The request_email function is used to send a confirmation email to the user.

    :param body: RequestEmail: Email of the user we want to confirm
    :param background_tasks: BackgroundTasks: Background task to run
    :param request: Request: The base url of the request
    :param db: Session: Connection to the database
    :return: A message that tells the user to check their email for confirmation
    """
    user = await repository_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {'message': 'Your email is already confirmed'}
    
    if user:
        background_tasks.add_task(send_email, user.email, user.username, str(request.base_url))

    return {'message': 'Check your email for confirmation.'}