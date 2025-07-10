import json
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from webmonitor.models import Space
from .models import SpaceModel

class SpaceRepository:
    """Repository for Space operations"""

    @staticmethod
    def _map_fields_to_db(space: Space, db_space: SpaceModel) -> None:
        db_space.name = space.name
        db_space.description = space.description
        db_space.updated_at = space.updated_at
        db_space.notification_emails = json.dumps(space.notification_emails) if space.notification_emails else None

    @staticmethod
    def _to_domain_model(db_space: SpaceModel) -> Space:
        notification_emails = json.loads(db_space.notification_emails) if db_space.notification_emails else []

        return Space(
            id=db_space.id,
            name=db_space.name,
            description=db_space.description,
            created_at=db_space.created_at,
            updated_at=db_space.updated_at,
            notification_emails=notification_emails
        )

    @staticmethod
    def _to_domain_models(db_spaces: List[SpaceModel]) -> List[Space]:
        spaces = []
        for db_space in db_spaces:
            spaces.append(SpaceRepository._to_domain_model(db_space))
        return spaces

    @staticmethod
    def save(session: Session, space: Space) -> Space:
        # Check if space already exists
        db_space = session.query(SpaceModel).filter(SpaceModel.id == space.id).first()

        if db_space:
            # Update existing space
            SpaceRepository._map_fields_to_db(space, db_space)
        else:
            # Create new space
            db_space = SpaceModel(
                id=space.id,
                created_at=space.created_at
            )
            SpaceRepository._map_fields_to_db(space, db_space)
            session.add(db_space)

        return space
    
    @staticmethod
    def get_by_id(session: Session, space_id: str) -> Optional[Space]:
        db_space = session.query(SpaceModel).filter(SpaceModel.id == space_id).first()
        if not db_space:
            return None

        return SpaceRepository._to_domain_model(db_space)
    
    @staticmethod
    def get_by_name(session: Session, name: str) -> Optional[Space]:
        db_space = session.query(SpaceModel).filter(SpaceModel.name == name).first()
        if not db_space:
            return None

        return SpaceRepository._to_domain_model(db_space)
    
    @staticmethod
    def list_all(session: Session) -> List[Space]:
        db_spaces = session.query(SpaceModel).all()
        return SpaceRepository._to_domain_models(db_spaces)
    
    @staticmethod
    def delete(session: Session, space_id: str) -> bool:
        db_space = session.query(SpaceModel).filter(SpaceModel.id == space_id).first()
        if not db_space:
            return False
        
        session.delete(db_space)
        return True