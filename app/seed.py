from datetime import date

from . import crud
from .database import Base, SessionLocal, engine
from .schemas import StudentCreate

DUMMY_STUDENTS = [
    ("Aarav Sharma", "2004-08-15", "Python Backend", "Delhi"),
    ("Diya Verma", "2006-05-20", "Web Development", "Mumbai"),
    ("Kabir Singh", "2007-09-02", "Python Backend", "Pune"),
    ("Ananya Gupta", "2003-01-10", "Data Science", "Jaipur"),
    ("Rohan Mehta", "2005-11-30", "Web Development", "Lucknow"),
    ("Saanvi Patel", "2008-03-18", "Data Science", "Hyderabad"),
    ("Arjun Reddy", "2002-12-25", "Python Backend", "Bengaluru"),
    ("Meera Iyer", "2006-07-07", "Machine Learning", "Chennai"),
]


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    for number, (name, dob, course, city) in enumerate(DUMMY_STUDENTS, start=1):
        data = StudentCreate(
            name=name,
            date_of_birth=dob,
            email=f"student{number}@example.com",
            phone=f"+9190000000{number:02d}",
            course=course,
            address=f"{city}, India",
            enrollment_date=date(2026, 7, 1),
        )
        try:
            crud.create_student(db, data)
        except Exception:
            db.rollback()
            print(f"Skipped {name} (already exists)")
    db.close()
    print("Dummy data added")


if __name__ == "__main__":
    main()
