from app import db
from app.modules.community.models import Community, CommunityCurator
from core.repositories.BaseRepository import BaseRepository


class CommunityRepository(BaseRepository):
    def __init__(self):
        super().__init__(Community)

    def get_by_name(self, name: str) -> Community:
        return self.model.query.filter_by(name=name).first()

    def get_all_communities(self) -> list[Community]:
        return self.model.query.all()


class CommunityCuratorRepository(BaseRepository):
    def __init__(self):
        super().__init__(CommunityCurator)

    def get_curators_by_community(self, community_id: int) -> list[CommunityCurator]:
        return self.model.query.filter_by(community_id=community_id).all()

    def get_communities_by_user(self, user_id: int) -> list[Community]:
        """Get all communities where user is a curator"""
        return Community.query.join(CommunityCurator).filter(CommunityCurator.user_id == user_id).all()

    def is_curator(self, user_id: int, community_id: int) -> bool:
        curator = self.model.query.filter_by(user_id=user_id, community_id=community_id).first()
        return curator is not None

    def add_curator(self, community_id: int, user_id: int):
        try:
            curator = CommunityCurator(community_id=community_id, user_id=user_id)
            db.session.add(curator)
            db.session.flush()
            print(f"Curator added: community_id={community_id}, user_id={user_id}")
            return curator
        except Exception as e:
            print(f"Error adding curator: {str(e)}")
            raise

    def remove_curator(self, community_id: int, user_id: int):
        curator = self.model.query.filter_by(community_id=community_id, user_id=user_id).first()
        if curator:
            return self.delete(curator)
        return None
