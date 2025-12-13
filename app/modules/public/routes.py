import logging
from datetime import datetime, timedelta

from flask import render_template, request

from app.modules.community.models import CommunityDataset
from app.modules.community.services import CommunityService
from app.modules.dataset.models import Author, DataSet, DSMetaData, DSMetrics, PublicationType
from app.modules.dataset.services import DataSetService
from app.modules.public import public_bp

logger = logging.getLogger(__name__)


@public_bp.route("/")
def index():
    logger.info("Access index")
    dataset_service = DataSetService()
    community_service = CommunityService()

    # Statistics: total datasets and CSV files
    datasets_counter = dataset_service.count_synchronized_datasets()
    csv_files_counter = dataset_service.total_csv_files()

    # Statistics: total downloads
    total_dataset_downloads = dataset_service.total_dataset_downloads()

    # Statistics: total views
    total_dataset_views = dataset_service.total_dataset_views()

    # Get all communities for the filter dropdown
    communities = community_service.get_all_communities()

    return render_template(
        "public/index.html",
        datasets=dataset_service.latest_synchronized(),
        datasets_counter=datasets_counter,
        csv_files_counter=csv_files_counter,
        total_dataset_downloads=total_dataset_downloads,
        total_dataset_views=total_dataset_views,
        communities=communities,
    )


@public_bp.route("/search", methods=["GET"])
def search_datasets():
    logger.info("Searching datasets with filters")
    community_service = CommunityService()

    query = DataSet.query.join(DSMetaData).filter(DSMetaData.dataset_doi.isnot(None))

    title = request.args.get("title", "").strip()
    if title:
        query = query.filter(DSMetaData.title.ilike(f"%{title}%"))
        logger.info(f"Filtering by title: {title}")

    author = request.args.get("author", "").strip()
    if author:
        query = query.outerjoin(Author).filter(Author.name.ilike(f"%{author}%"))
        logger.info(f"Filtering by author: {author}")

    tags = request.args.get("tags", "").strip()
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        for tag in tag_list:
            query = query.filter(DSMetaData.tags.ilike(f"%{tag}%"))
        logger.info(f"Filtering by tags: {tag_list}")

    pub_type = request.args.get("publication_type", "").strip()
    if pub_type:
        try:
            for enum_member in PublicationType:
                pub_type_enum = None
                if enum_member.value == pub_type.lower():
                    pub_type_enum = enum_member
                    break

            if pub_type_enum:
                query = query.filter(DSMetaData.publication_type == pub_type_enum)
                logger.info(f"Filtering by publication_type: {pub_type} -> {pub_type_enum.name}")
            else:
                logger.warning(f"Publication type '{pub_type}' not found in enum")
        except Exception as e:
            logger.warning(f"Error filtering by publication_type '{pub_type}': {e}")

    # Community filter
    selected_community = None
    community_id = request.args.get("community", "").strip()
    if community_id:
        try:
            community_id_int = int(community_id)
            query = query.join(CommunityDataset).filter(CommunityDataset.community_id == community_id_int)
            selected_community = community_service.get_by_id(community_id_int)
            logger.info(f"Filtering by community_id: {community_id_int}")
        except ValueError:
            logger.warning(f"Invalid community_id format: {community_id}")

    date_from = request.args.get("date_from")
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(DataSet.created_at >= date_from_obj)
            logger.info(f"Filtering from date: {date_from}")
        except ValueError:
            logger.warning(f"Invalid date format for date_from: {date_from}")

    date_to = request.args.get("date_to")
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")
            date_to_obj = date_to_obj + timedelta(days=1)
            query = query.filter(DataSet.created_at < date_to_obj)
            logger.info(f"Filtering to date: {date_to}")
        except ValueError as e:
            logger.warning(f"Invalid date format for date_to: {date_to}. Error: {e}")

    # Filter by engine size (average motor size)
    engine_size_min = request.args.get("engine_size_min", "").strip()
    engine_size_max = request.args.get("engine_size_max", "").strip()

    if engine_size_min and engine_size_max:
        try:
            min_val = float(engine_size_min)
            max_val = float(engine_size_max)
            query = query.filter(DSMetaData.ds_metrics.has(DSMetrics.average_engine_size.between(min_val, max_val)))
            logger.info(f"Filtering by engine size between {min_val} and {max_val}")
        except ValueError:
            logger.warning(f"Invalid engine size values: min={engine_size_min}, max={engine_size_max}")
    elif engine_size_min:
        try:
            min_val = float(engine_size_min)
            query = query.filter(DSMetaData.ds_metrics.has(DSMetrics.average_engine_size >= min_val))
            logger.info(f"Filtering by minimum engine size: {min_val}")
        except ValueError:
            logger.warning(f"Invalid engine size value for min: {engine_size_min}")
    elif engine_size_max:
        try:
            max_val = float(engine_size_max)
            query = query.filter(DSMetaData.ds_metrics.has(DSMetrics.average_engine_size <= max_val))
            logger.info(f"Filtering by maximum engine size: {max_val}")
        except ValueError:
            logger.warning(f"Invalid engine size value for max: {engine_size_max}")

    # Filter by consumption (average consumption)
    consumption_min = request.args.get("consumption_min", "").strip()
    consumption_max = request.args.get("consumption_max", "").strip()

    if consumption_min and consumption_max:
        try:
            min_val = float(consumption_min)
            max_val = float(consumption_max)
            query = query.filter(DSMetaData.ds_metrics.has(DSMetrics.average_consumption.between(min_val, max_val)))
            logger.info(f"Filtering by consumption between {min_val} and {max_val}")
        except ValueError:
            logger.warning(f"Invalid consumption values: min={consumption_min}, max={consumption_max}")
    elif consumption_min:
        try:
            min_val = float(consumption_min)
            query = query.filter(DSMetaData.ds_metrics.has(DSMetrics.average_consumption >= min_val))
            logger.info(f"Filtering by minimum consumption: {min_val}")
        except ValueError:
            logger.warning(f"Invalid consumption value for min: {consumption_min}")
    elif consumption_max:
        try:
            max_val = float(consumption_max)
            query = query.filter(DSMetaData.ds_metrics.has(DSMetrics.average_consumption <= max_val))
            logger.info(f"Filtering by maximum consumption: {max_val}")
        except ValueError:
            logger.warning(f"Invalid consumption value for max: {consumption_max}")

    datasets = query.order_by(DataSet.created_at.desc()).distinct().all()

    logger.info(f"Found {len(datasets)} datasets matching search criteria")

    # Get all communities for the filter dropdown
    communities = community_service.get_all_communities()

    return render_template(
        "public/search_results.html",
        datasets=datasets,
        search_params=request.args.to_dict(),
        communities=communities,
        selected_community=selected_community,
    )
