from app import db
from app.modules.community.models import Community, CommunityCurator
from app.modules.community.repositories import CommunityRepository, CommunityCuratorRepository
from core.services.BaseService import BaseService
from typing import Optional


class CommunityService(BaseService):
    def __init__(self):
        super().__init__(CommunityRepository())
        self.curator_repository = CommunityCuratorRepository()

    def create_community(self, name: str, description: str, creator_id: int, logo: Optional[str] = None) -> Community:

        created_community = self.repository.create(
            name=name,
            description=description,
            logo=logo)

        # Asegurar que se hace flush para obtener el ID
        db.session.flush()

        self.curator_repository.add_curator(created_community.id, creator_id)

        # Commit explícito
        db.session.commit()

        return created_community

    def update_community(
            self,
            community_id: int,
            name: Optional[str] = None,
            description: Optional[str] = None,
            logo: Optional[str] = None) -> Community:
        community = self.get_by_id(community_id)
        if not community:
            raise ValueError(f"Community with id {community_id} not found")

        if name:
            community.name = name
        if description is not None:
            community.description = description
        if logo is not None:
            community.logo = logo

        return self.update(community)

    def delete_community(self, community_id: int) -> bool:
        community = self.get_by_id(community_id)
        if not community:
            raise ValueError(f"Community with id {community_id} not found")

        # BaseService.delete expects an id; pass the community_id (not the object)
        return self.delete(community_id)

    def get_community_by_name(self, name: str) -> Optional[Community]:
        return self.repository.get_by_name(name)

    def get_all_communities(self) -> list[Community]:
        return self.repository.get_all_communities()

    def get_community_curators(self, community_id: int) -> list[CommunityCurator]:
        return self.curator_repository.get_curators_by_community(community_id)

    def get_user_communities(self, user_id: int) -> list[Community]:
        return self.curator_repository.get_communities_by_user(user_id)

    def add_curator(self, community_id: int, user_id: int, requester_id: int = None) -> CommunityCurator:
        """
        Add a curator to a community. requester_id is optional and represents the user performing the action.
        """
        # Optional: could add auditing using requester_id in future
        try:
            curator = self.curator_repository.add_curator(community_id, user_id)
            # ensure persistence
            db.session.commit()
            return curator
        except Exception:
            # rollback on error and re-raise so callers can react
            db.session.rollback()
            raise

    def remove_curator(self, community_id: int, user_id: int, requester_id: int):
        curators = self.curator_repository.get_curators_by_community(community_id)
        if len(curators) <= 1:
            raise ValueError("Cannot remove the last curator from a community")

        return self.curator_repository.remove_curator(community_id, user_id)

    def is_curator(self, user_id: int, community_id: int) -> bool:
        return self.curator_repository.is_curator(user_id, community_id)
