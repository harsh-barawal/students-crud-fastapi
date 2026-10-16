import re
from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

PHONE_PATTERN = r"^\+?[0-9]{10,15}$"


def check_name(name):
    name = " ".join(name.split())
    if not re.fullmatch(r"[A-Za-z .'-]+", name):
        raise ValueError("Name can only contain letters, spaces, . ' and -")
    return name


def check_dob(dob):
    if dob >= date.today():
        raise ValueError("Date of birth must be in the past")
    if dob.year < 1950:
        raise ValueError("Date of birth is too old")
    return dob


class StudentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    date_of_birth: date
    email: EmailStr | None = None
    phone: str | None = Field(default=None, pattern=PHONE_PATTERN)
    course: str | None = None
    address: str | None = None
    enrollment_date: date | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        return check_name(value)

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, value):
        return check_dob(value)

    @model_validator(mode="after")
    def validate_contact(self):
        if not self.email and not self.phone:
            raise ValueError("Give at least one contact: email or phone")
        return self


class StudentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    date_of_birth: date | None = None
    email: EmailStr | None = None
    phone: str | None = Field(default=None, pattern=PHONE_PATTERN)
    course: str | None = None
    address: str | None = None
    enrollment_date: date | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        return check_name(value) if value else value

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, value):
        return check_dob(value) if value else value


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: str
    name: str
    date_of_birth: date
    age: int
    email: str | None
    phone: str | None
    course: str | None
    address: str | None
    enrollment_date: date | None


class StudentList(BaseModel):
    total: int
    page: int
    limit: int
    students: list[StudentResponse]


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=500)
