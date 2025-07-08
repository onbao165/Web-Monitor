from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
import json
import uuid

@dataclass
class Space:
    # Represents a space in the database
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    notification_emails: List[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.notification_emails is None:
            self.notification_emails = []

    def update_timestamp(self):
        self.updated_at = datetime.now()
    
    def add_notification_email(self, email: str):
        self.notification_emails.append(email)
        self.update_timestamp()

    def to_dict(self)->dict:
        # Converts the space object to a dictionary
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'notification_emails': self.notification_emails
        }
    
    @classmethod
    def from_dict(cls, data: dict)->'Space':
        # Converts a dictionary to a space object
        space = cls(
            id=data['id'],
            name=data['name'],
            # Use get() to avoid KeyError if the key is not present
            description=data.get('description'),
            created_at= datetime.fromisoformat(data['created_at']),
            notification_emails=data['notification_emails']
        )
        if (data.get('updated_at')):
            space.updated_at = datetime.fromisoformat(data['updated_at'])
        return space