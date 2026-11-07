from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.errors import AppError
from app.extensions import db
from app.models import User
from app.security import hash_password, verify_password


def register_user(name: str, email: str, password: str) -> User:
    if db.session.scalar(select(User).where(User.email == email)):
        raise AppError("E-mail já cadastrado.", 409, "email_taken")

    user = User(name=name, email=email, password_hash=hash_password(password))
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:  # duas requisições ao mesmo tempo com o mesmo e-mail
        db.session.rollback()
        raise AppError("E-mail já cadastrado.", 409, "email_taken")
    return user


def authenticate(email: str, password: str) -> User:
    user = db.session.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(user.password_hash, password):
        raise AppError("E-mail ou senha incorretos.", 401, "invalid_credentials")
    return user