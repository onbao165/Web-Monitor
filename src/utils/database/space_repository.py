import json
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from src.models.space import Space
from .models import SpaceModel

class SpaceRepository:
    """Repository for Space operations"""
    
    @staticmethod
    def save(session: Session, space: Space) -> Space:
        """Save a space to the database"""
        # Convert notification_emails list to JSON string
        notification_emails_json = json.dumps(space.notification_emails) if space.notification_emails else None
        
        # Check if space already exists
        db_space = session.query(SpaceModel).filter(SpaceModel.id == space.id).first()
        
        if db_space:
            # Update existing space
            db_space.name = space.name
            db_space.description = space.description
            db_space.updated_at = datetime.now()
            db_space.notification_emails = notification_emails_json
        else:
            # Create new space
            db_space = SpaceModel(
                id=space.id,
                name=space.name,
                description=space.description,
                created_at=space.created_at,
                updated_at=space.updated_at,
                notification_emails=notification_emails_json
            )
            session.add(db_space)
        
        return space
    
    @staticmethod
    def get_by_id(session: Session, space_id: str) -> Optional[Space]:
        """Get a space by ID"""
        db_space = session.query(SpaceModel).filter(SpaceModel.id == space_id).first()
        if not db_space:
            return None
        
        # Convert JSON string back to list
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
    def get_by_name(session: Session, name: str) -> Optional[Space]:
        """Get a space by name"""
        db_space = session.query(SpaceModel).filter(SpaceModel.name == name).first()
        if not db_space:
            return None
        
        # Convert JSON string back to list
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
    def list_all(session: Session) -> List[Space]:
        """List all spaces"""
        db_spaces = session.query(SpaceModel).all()
        spaces = []
        
        for db_space in db_spaces:
            # Convert JSON string back to list
            notification_emails = json.loads(db_space.notification_emails) if db_space.notification_emails else []
            
            spaces.append(Space(
                id=db_space.id,
                name=db_space.name,
                description=db_space.description,
                created_at=db_space.created_at,
                updated_at=db_space.updated_at,
                notification_emails=notification_emails
            ))
        
        return spaces
    
    @staticmethod
    def delete(session: Session, space_id: str) -> bool:
        """Delete a space by ID"""
        db_space = session.query(SpaceModel).filter(SpaceModel.id == space_id).first()
        if not db_space:
            return False
        
        session.delete(db_space)
        return True