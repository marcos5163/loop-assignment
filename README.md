# loop-assignment

This is django project named **loop_assignment**, using postgres as database, celery as distributed queue, redis as messeging borker for celery and django ORM for quering db.

- [db_schema](https://github.com/marcos5163/loop-assignment/blob/master/app/models.py), Here **StoreObservation** is used for storing observation data,
   **StoreBusinessHours** for store's business hours, **StoreTimezone** for store's native timezone. and **Report** for report generation related data like status, generation retry count etc.
- [data_ingestion_view](https://github.com/marcos5163/loop-assignment/blob/master/app/views/data_ingestion_views.py) basically takes csv's as input and populate StoreObservation, StoreBusinessHour and StoreTimezone tables.
  
  
  
  
  
