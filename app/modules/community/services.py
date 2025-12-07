from typing import Optional

from app import db
from app.modules.community.models import Community, CommunityCurator
from app.modules.community.repositories import CommunityCuratorRepository, CommunityRepository, CommunityDatasetRepository
from core.services.BaseService import BaseService


class CommunityService(BaseService):
    def __init__(self):
        super().__init__(CommunityRepository())
        self.curator_repository = CommunityCuratorRepository()
        self.dataset_repository = CommunityDatasetRepository()

    def create_community(self, name: str, description: str, creator_id: int, logo: Optional[str] = None) -> Community:

        created_community = self.repository.create(name=name, description=description, logo=logo)

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
        logo: Optional[str] = None,
    ) -> Community:
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

    def assign_dataset_to_community(self, community_id: int, dataset_id: int, curator_id: int):
        """
        Assign a dataset to a community.
        Only curators of the community can perform this action.
        """
        if not self.is_curator(curator_id, community_id):
            raise PermissionError("Only curators can assign datasets to this community")
        
        # Check if already assigned
        if self.dataset_repository.is_dataset_assigned(community_id, dataset_id):
            raise ValueError("Dataset is already assigned to this community")
        
        try:
            assignment = self.dataset_repository.assign_dataset(community_id, dataset_id, curator_id)
            db.session.commit()
            return assignment
        except Exception:
            db.session.rollback()
            raise

    def unassign_dataset_from_community(self, community_id: int, dataset_id: int, curator_id: int):
        """
        Remove a dataset from a community.
        Only curators of the community can perform this action.
        """
        if not self.is_curator(curator_id, community_id):
            raise PermissionError("Only curators can unassign datasets from this community")
        
        try:
            result = self.dataset_repository.unassign_dataset(community_id, dataset_id)
            db.session.commit()
            return result
        except Exception:
            db.session.rollback()
            raise

    def get_community_datasets(self, community_id: int):
        """Get all datasets assigned to a community"""
        return self.dataset_repository.get_community_datasets(community_id)

    def get_available_datasets_for_community(self, community_id: int):
        """Get datasets that are not yet assigned to this community"""
        from app.modules.dataset.models import DataSet
        
        # Get all dataset IDs already assigned to this community
        assigned_dataset_ids = [
            assignment.dataset_id 
            for assignment in self.dataset_repository.get_community_datasets(community_id)
        ]
        
        # Query all datasets not in the assigned list
        if assigned_dataset_ids:
            available_datasets = DataSet.query.filter(~DataSet.id.in_(assigned_dataset_ids)).all()
        else:
            available_datasets = DataSet.query.all()
        
        return available_datasets
