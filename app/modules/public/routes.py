import logging
from datetime import datetime, timedelta

from flask import render_template, request

from app.modules.dataset.models import Author, DataSet, DSMetaData, PublicationType
from app.modules.dataset.services import DataSetService
from app.modules.featuremodel.services import FeatureModelService
from app.modules.public import public_bp

logger = logging.getLogger(__name__)


@public_bp.route("/")
def index():
    logger.info("Access index")
    dataset_service = DataSetService()
    feature_model_service = FeatureModelService()

    # Statistics: total datasets and feature models
    datasets_counter = dataset_service.count_synchronized_datasets()
    feature_models_counter = feature_model_service.count_feature_models()

    # Statistics: total downloads
    total_dataset_downloads = dataset_service.total_dataset_downloads()
    total_feature_model_downloads = feature_model_service.total_feature_model_downloads()

    # Statistics: total views
    total_dataset_views = dataset_service.total_dataset_views()
    total_feature_model_views = feature_model_service.total_feature_model_views()

    return render_template(
        "public/index.html",
        datasets=dataset_service.latest_synchronized(),
        datasets_counter=datasets_counter,
        feature_models_counter=feature_models_counter,
        total_dataset_downloads=total_dataset_downloads,
        total_feature_model_downloads=total_feature_model_downloads,
        total_dataset_views=total_dataset_views,
        total_feature_model_views=total_feature_model_views,
    )


@public_bp.route("/search", methods=["GET"])
def search_datasets():
    logger.info("Searching datasets with filters")

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

    datasets = query.order_by(DataSet.created_at.desc()).distinct().all()

    logger.info(f"Found {len(datasets)} datasets matching search criteria")

    return render_template("public/search_results.html", datasets=datasets, search_params=request.args.to_dict())
