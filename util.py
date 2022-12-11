import hashlib
from typing import NewType
from telegram import User

QuestionKey = NewType('QuestionKey', str)


def hash_string(s: str) -> QuestionKey:
    return QuestionKey(hashlib.sha256(bytes(s.encode())).hexdigest()[:16])


def with_default(s: str = ""):
    return s


def get_user_familiar(user: User) -> str:
    return f'{with_default(user.first_name)} {with_default(user.last_name)}'

