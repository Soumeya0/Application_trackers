from datetime import date

from sqlalchemy import Column, Date, Integer, String, Text

from .database import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True)
    company = Column(String, nullable=False)
    role = Column(String, nullable=False)
    date_applied = Column(Date, nullable=False, default=date.today)
    status = Column(String, nullable=False, default="applied")
    deadline = Column(Date, nullable=True)
    follow_up_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    job_link = Column(String, nullable=True)
    tech_tags = Column(String, nullable=True)
    # Set once, the first time status moves away from "applied" — used for time-to-response stats.
    responded_at = Column(Date, nullable=True)

    def __repr__(self):
        return f"<Application id={self.id} {self.company!r} - {self.role!r} ({self.status})>"
