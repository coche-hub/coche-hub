from app.modules.explore.repositories import ExploreRepository
from core.services.BaseService import BaseService


class ExploreService(BaseService):
    def __init__(self):
        super().__init__(ExploreRepository())

    def filter(
        self,
        title="",
        author="",
        tags="",
        community="",
        publication_type="",
        date_from="",
        date_to="",
        engine_size_min="",
        engine_size_max="",
        consumption_min="",
        consumption_max="",
        sorting="newest",
        **kwargs,
    ):
        return self.repository.filter(
            title,
            author,
            tags,
            community,
            publication_type,
            date_from,
            date_to,
            engine_size_min,
            engine_size_max,
            consumption_min,
            consumption_max,
            sorting,
            **kwargs,
        )
