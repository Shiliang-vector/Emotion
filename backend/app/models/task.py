from __future__ import annotations

from datetime import datetime

from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    role: Mapped[str] = mapped_column(String(24), nullable=False, default="client")
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    tasks: Mapped[list["AnalysisTask"]] = relationship(back_populates="user")


class ConsultationBinding(Base):
    __tablename__ = "consultation_bindings"
    __table_args__ = (UniqueConstraint("counselor_id", "client_id", name="uq_counselor_client"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    counselor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class AnalysisTask(Base):
    __tablename__ = "analysis_tasks"

    task_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="queued")
    stage: Mapped[str] = mapped_column(String(48), nullable=False, default="queued")
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    message: Mapped[str] = mapped_column(String(240), nullable=False, default="任务已创建，等待处理")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="tasks")
    report: Mapped[ReportRecord | None] = relationship(back_populates="task", uselist=False)


class ReportRecord(Base):
    __tablename__ = "report_records"

    task_id: Mapped[str] = mapped_column(ForeignKey("analysis_tasks.task_id"), primary_key=True)
    report_json: Mapped[str] = mapped_column(Text, nullable=False)
    expert_advice: Mapped[str] = mapped_column(Text, nullable=False)
    counselor_assistance: Mapped[str | None] = mapped_column(Text, nullable=True)
    counselor_assistance_created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    task: Mapped[AnalysisTask] = relationship(back_populates="report")


class CounselorNote(Base):
    __tablename__ = "counselor_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    counselor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
