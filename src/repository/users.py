from libgravatar import Gravatar
from sqlalchemy.orm import Session

from src.database.models import User
from src.schemas import UserModel


async def get_user_by_email(email: str, db: Session) -> User:
    """
    The get_user_by_email function takes in an email and a database session,
    and returns the user associated with that email. If no such user exists,
    it will return None.

    :param email: str: Email of the user we want to get
    :param db: Session: Connection to the database
    :return: The first user found in the database that matches the given email
    """
    return db.query(User).filter(User.email == email).first()


async def create_user(body: UserModel, db: Session) -> User:

    """
    The create_user function creates a new user in the database.

    :param body: UserModel: Information to create a user
    :param db: Session: Connection to the database
    :return: A user object
    """
    avatar = None

    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as e:
        print(e)
        
    new_user = User(**body.model_dump(), avatar=avatar)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: Session) -> None:
    """
    The update_token function updates the token for a user.

    :param user: User: User for whom the token needs to be updated
    :param token: str | None: The refreshed token
    :param db: Session: Connection to the database
    :return: None
    """
    user.refresh_token = token
    db.commit()


async def confirmed_email(email: str, db: Session) -> None:
    """
    The confirmed_email function takes in an email and a database session,
    and sets the confirmed field of the user with that email to True.

    :param email: str: Email of the user we want to confirm
    :param db: Session: Connection to the database
    :return: None
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    db.commit()


async def update_avatar_url(email: str, url: str | None, db: Session) -> User:
    """
    The update_avatar_url function updates the avatar url of a user.

    :param email: str: Email of the user whose avatar needs to be changed
    :param url: str | None: New avatar url
    :param db: Session: Connection to the database
    :return: The updated user
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    db.commit()
    return user