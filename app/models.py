from django.db import models

class StoreObservations(models.Model):
    store_id = models.CharField(max_length=200)
    timestamp_utc = models.DateTimeField(db_index=True)
    status = models.BooleanField(db_index=True)

    class Meta:
      unique_together = ('store_id', 'timestamp_utc')


class StoreBusinessHours(models.Model):
    store_id=  models.CharField(max_length=200, db_index=True)
    day_of_week = models.IntegerField(db_index=True)
    start_time_local= models.TimeField(db_index = True)
    end_time_local = models.TimeField(db_index=True)


class StoreTimezone(models.Model):
    store_id = models.CharField(max_length=200, unique=True, db_index=True)
    timezone_str = models.CharField(max_length=200, db_index=True)

class Report(models.Model):
    
    INITIATED = "INITIATED"
    IN_PROCESS = "IN_PROCESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"  

    REPORT_STATUSES = ((INITIATED, "INITIATED"), (IN_PROCESS, "IN_PROCESS"), (COMPLETED, "COMPLETED"), (FAILED, "FAILED"))

    report_id = models.CharField(max_length=200)
    status = models.CharField(choices = REPORT_STATUSES, max_length=100)
    report_link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    generation_retry_count = models.IntegerField(default=0)

