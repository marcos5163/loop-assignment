from django.urls import path


from  app.views.data_ingestion_views import StoreDataIngestionViewSet
from app.views.report_generation_views import ReportGenerationViewSet

urlpatterns = [
    path("ingest-store-observations/", StoreDataIngestionViewSet.as_view({"post":"store_observation_data_ingestion"}), name = "store_observation_data_ingestion_api_view"),
    path("ingest-store-business-hours/", StoreDataIngestionViewSet.as_view({"post":"store_business_hours_data_ingestion"}), name = "store_business_hours_data_ingestion_api_view"),
    path("ingest-store-timezones/", StoreDataIngestionViewSet.as_view({"post":"store_timezone_data_ingestion"}), name = "store_timezone_data_ingestion_api_view"),
    path("trigger-report/", ReportGenerationViewSet.as_view({"get":"trigger_report_generation"}), name = "trigger_report_api_view"),
    path("get-report/", ReportGenerationViewSet.as_view({"post": "report_generation_status"}), name = "report_generation_status_api_view")
]


