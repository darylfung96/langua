"""
Generic base service providing common CRUD operations for SQLAlchemy models.

Each domain service subclasses BaseService and overrides only the logic that
differs (e.g. saving associated files, JSON field validation).
"""
import logging
from typing import Generic, List, Optional, Type, TypeVar

from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import Base

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Base)


class BaseService(Generic[T]):
    """Generic service for CRUD operations on a single SQLAlchemy model."""

    model: Type[T]

    # Subclasses may set this to the column used for ordering list results.
    order_column: str = "created_at"

    def get_all(
        self,
        db: Session,
        user_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[T]:
        """Return records for the given user, newest first, with optional pagination."""
        try:
            order_col = getattr(self.model, self.order_column)
            query = (
                db.query(self.model)
                .filter(self.model.user_id == user_id)
                .order_by(desc(order_col))
            )
            if offset:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)
            return query.all()
        except Exception as e:
            logger.error(f"Error fetching {self.model.__name__} list: {e}")
            raise

    def get_by_id(self, record_id: str, db: Session, user_id: str) -> T:
        """Return a record by primary key scoped to the given user, or raise ValueError."""
        try:
            record = (
                db.query(self.model)
                .filter(self.model.id == record_id, self.model.user_id == user_id)
                .first()
            )
            if not record:
                raise ValueError(f"{self.model.__name__} with ID {record_id} not found")
            return record
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error fetching {self.model.__name__} {record_id}: {e}")
            raise

    def delete(self, record_id: str, db: Session, user_id: str) -> bool:
        """Delete a record by primary key scoped to the given user."""
        try:
            record = self.get_by_id(record_id, db, user_id)
            self._pre_delete(record)
            db.delete(record)
            db.commit()
            return True
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting {self.model.__name__} {record_id}: {e}")
            raise

    def _pre_delete(self, record: T) -> None:
        """Hook called before the record is deleted.  Override to delete files etc."""
