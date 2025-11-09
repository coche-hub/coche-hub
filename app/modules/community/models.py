from datetime import datetime

from app import db


class Community(db.Model):
    __tablename__ = "community"

    # Columns
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    logo = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    curators = db.relationship("CommunityCurator", back_populates="community", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Community {self.name}>"

    def __init__(self, name: str, description: str = None, logo: str = None):
        self.name = name
        self.description = description
        self.logo = logo


class CommunityCurator(db.Model):
    __tablename__ = "community_curator"

    # Columns
    id = db.Column(db.Integer, primary_key=True)
    community_id = db.Column(db.Integer, db.ForeignKey("community.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    community = db.relationship("Community", back_populates="curators")
    user = db.relationship("User", backref="curated_communities")

    __table_args__ = (db.UniqueConstraint("community_id", "user_id", name="unique_community_curator"),)

    def __repr__(self):
        return f"<CommunityCurator community_id={self.community_id} user_id={self.user_id}>"
