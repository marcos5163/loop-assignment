from rest_framework import viewsets
import csv
from app.models import StoreObservations, StoreBusinessHours, StoreTimezone
from datetime import datetime, time, timezone
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.utils import timezone


class StoreDataIngestionViewSet(viewsets.ViewSet):
    
    def store_observation_data_ingestion(self, request):
        
        input_csv_file = request.data['store_observations']

        csv_data = input_csv_file.read().decode('utf-8')
        csv_reader  = csv.reader(csv_data.splitlines(), delimiter=',')
        
        store_observations = []

        existing_timestamp_to_store_id_map = {}

        existing_store_observations_queryset  = list(StoreObservations.objects.all())

        for observations in existing_store_observations_queryset:
            existing_timestamp_to_store_id_map[(observations.timestamp_utc, observations.store_id)] = True
        
        next(csv_reader)

        for row in csv_reader:
            
            date_str = row[2].replace(' UTC', '')
      
            timestamp_utc_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f' if '.' in date_str else '%Y-%m-%d %H:%M:%S')
            timestamp_utc_obj = timezone.make_aware(timestamp_utc_obj, timezone=timezone.utc)
            store_id = row[0]
            if existing_timestamp_to_store_id_map.get((timestamp_utc_obj, store_id)):
                continue
            
            
            store_observations.append(StoreObservations(store_id = store_id, status = True if row[1]== 'active' else False, timestamp_utc = timestamp_utc_obj))

         
        StoreObservations.objects.bulk_create(store_observations, batch_size=200)    
        
        return  Response(status=HTTP_200_OK, data={}) 


    def store_business_hours_data_ingestion(self, request):

        input_csv_file = request.data['menu_hours']

        csv_data = input_csv_file.read().decode('utf-8')
        csv_reader  = csv.reader(csv_data.splitlines(), delimiter=',')
        
        stores_with_business_hours = []

        existing_stores = list(StoreBusinessHours.objects.all().values_list('store_id', flat=True))

        next(csv_reader)

        for row in csv_reader:
            if row[0] in existing_stores:
                continue

            
            start_time = row[2].split(':')
            end_time = row[3].split(':')
            stores_with_business_hours.append(StoreBusinessHours(store_id = row[0], 
                                                            day_of_week = row[1], 
                                                            start_time_local = time(int(start_time[0]), int(start_time[1]), int(start_time[2]), tzinfo= timezone.utc ), 
                                                            end_time_local = time(int(end_time[0]), int(end_time[1]), int(end_time[2]), tzinfo= timezone.utc)
                                                            ))
                
        StoreBusinessHours.objects.bulk_create(stores_with_business_hours, batch_size=500)

        return Response(status=HTTP_200_OK, data={})     


    def store_timezone_data_ingestion(self, request):

        input_csv_file = request.data['timezones']

        csv_data = input_csv_file.read().decode('utf-8')
        csv_reader  = csv.reader(csv_data.splitlines(), delimiter=',')

        stores_with_timezones = []

        existing_store_timezones = list(StoreTimezone.objects.all().values_list('store_id', flat=True))

        next(csv_reader)

        for row in csv_reader:

            if row[0] in existing_store_timezones:
                continue

            stores_with_timezones.append(StoreTimezone(store_id = row[0], timezone_str = row[1]))

        StoreTimezone.objects.bulk_create(stores_with_timezones, batch_size=500)    

        return Response(status=HTTP_200_OK, data={})