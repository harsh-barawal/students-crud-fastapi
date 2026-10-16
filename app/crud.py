from datetime import date

from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .models import Student

SORT_COLUMNS = {
    "name": Student.name,
    "date_of_birth": Student.date_of_birth,
    "enrollment_date": Student.enrollment_date,
    "id": Student.id,
}


def get_student(db: Session, student_id: str):
    student = db.query(Student).filter(Student.student_id == student_id.upper()).first()
    if student is None:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
    return student


def check_duplicate(db: Session, email, phone, ignore_id=None):
    for column, value in (("email", email), ("phone", phone)):
        if not value:
            continue
        query = db.query(Student).filter(getattr(Student, column) == value)
        if ignore_id:
            query = query.filter(Student.id != ignore_id)
        if query.first():
            raise HTTPException(status_code=409, detail=f"A student with this {column} already exists")


def create_student(db: Session, data):
    values = data.model_dump()
    values["email"] = values["email"].lower() if values["email"] else None
    values["enrollment_date"] = values["enrollment_date"] or date.today()
    check_duplicate(db, values["email"], values["phone"])

    student = Student(**values)
    db.add(student)
    db.flush()
    student.student_id = f"EWB{date.today().year}{student.id:04d}"
    db.commit()
    db.refresh(student)
    return student


def get_students(db: Session, search=None, course=None, born_after=None, born_before=None,
                 sort_by="id", order="asc", page=1, limit=10):
    query = db.query(Student)

    if search:
        like = f"%{search}%"
        query = query.filter(or_(
            Student.name.ilike(like),
            Student.email.ilike(like),
            Student.student_id.ilike(like),
        ))
    if course:
        query = query.filter(func.lower(Student.course) == course.lower())
    if born_after:
        query = query.filter(Student.date_of_birth >= born_after)
    if born_before:
        query = query.filter(Student.date_of_birth <= born_before)

    total = query.count()
    column = SORT_COLUMNS.get(sort_by, Student.id)
    column = column.desc() if order == "desc" else column.asc()
    students = query.order_by(column).offset((page - 1) * limit).limit(limit).all()
    return students, total


def update_student(db: Session, student_id: str, changes: dict):
    student = get_student(db, student_id)

    if not changes:
        raise HTTPException(status_code=422, detail="No fields given to update")
    if changes.get("name", "x") is None or changes.get("date_of_birth", "x") is None:
        raise HTTPException(status_code=422, detail="name and date_of_birth cannot be empty")

    if changes.get("email"):
        changes["email"] = changes["email"].lower()
    email = changes.get("email", student.email)
    phone = changes.get("phone", student.phone)
    if not email and not phone:
        raise HTTPException(status_code=422, detail="Student must have at least one of email or phone")

    check_duplicate(db, changes.get("email"), changes.get("phone"), ignore_id=student.id)

    for field, value in changes.items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


def delete_student(db: Session, student_id: str):
    student = get_student(db, student_id)
    db.delete(student)
    db.commit()
