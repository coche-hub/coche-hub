from datetime import datetime, timedelta

from app.modules.community.models import CommunityDataset
from app.modules.dataset.models import Author, DataSet, DSMetaData, DSMetrics, PublicationType
from core.repositories.BaseRepository import BaseRepository


class ExploreRepository(BaseRepository):
    def __init__(self):
        super().__init__(DataSet)

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
        # Start with base query that ensures dataset_doi is not null
        query = DataSet.query.join(DSMetaData).filter(DSMetaData.dataset_doi.isnot(None))

        # Filter by title
        if title:
            query = query.filter(DSMetaData.title.ilike(f"%{title}%"))

        # Filter by author
        if author:
            query = query.outerjoin(Author).filter(Author.name.ilike(f"%{author}%"))

        # Filter by tags (comma-separated)
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
            for tag in tag_list:
                query = query.filter(DSMetaData.tags.ilike(f"%{tag}%"))

        # Filter by community
        if community:
            try:
                community_id_int = int(community)
                query = query.join(CommunityDataset).filter(CommunityDataset.community_id == community_id_int)
            except ValueError:
                pass

        # Filter by publication type
        if publication_type and publication_type != "":
            try:
                pub_type_enum = None
                for enum_member in PublicationType:
                    if enum_member.value.lower() == publication_type.lower():
                        pub_type_enum = enum_member
                        break

                if pub_type_enum:
                    query = query.filter(DSMetaData.publication_type == pub_type_enum)
            except Exception:
                pass

        # Filter by date_from
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
                query = query.filter(DataSet.created_at >= date_from_obj)
            except ValueError:
                pass

        # Filter by date_to
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")
                date_to_obj = date_to_obj + timedelta(days=1)
                query = query.filter(DataSet.created_at < date_to_obj)
            except ValueError:
                pass

        # Filter by engine size (average motor size)
        if engine_size_min and engine_size_max:
            try:
                min_val = float(engine_size_min)
                max_val = float(engine_size_max)
                query = query.filter(DSMetaData.ds_metrics.has(DSMetrics.average_engine_size.between(min_val, max_val)))
            except ValueError:
                pass
        elif engine_size_min:
            try:
                min_val = float(engine_size_min)
                query = query.filter(DSMetaData.ds_metrics.has(DSMetrics.average_engine_size >= min_val))
            except ValueError:
                pass
        elif engine_size_max:
            try:
                max_val = float(engine_size_max)
                query = query.filter(DSMetaData.ds_metrics.has(DSMetrics.average_engine_size <= max_val))
            except ValueError:
                pass

        # Filter by consumption (average consumption)
        if consumption_min and consumption_max:
            try:
                min_val = float(consumption_min)
                max_val = float(consumption_max)
                query = query.filter(DSMetaData.ds_metrics.has(DSMetrics.average_consumption.between(min_val, max_val)))
            except ValueError:
                pass
        elif consumption_min:
            try:
                min_val = float(consumption_min)
                query = query.filter(DSMetaData.ds_metrics.has(DSMetrics.average_consumption >= min_val))
            except ValueError:
                pass
        elif consumption_max:
            try:
                max_val = float(consumption_max)
                query = query.filter(DSMetaData.ds_metrics.has(DSMetrics.average_consumption <= max_val))
            except ValueError:
                pass

        # Order by created_at
        if sorting == "oldest":
            query = query.order_by(DataSet.created_at.asc())
        else:
            query = query.order_by(DataSet.created_at.desc())

        return query.distinct().all()
