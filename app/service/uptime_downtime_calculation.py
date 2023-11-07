from app.models import StoreObservations, StoreBusinessHours, StoreTimezone
from django.db.models import Max
from pytz import timezone
from datetime import timedelta, datetime


           

class UptimeDowntimeCalculationService:

    """
    This service is responsible for calculating uptime and downtime over different periods.

     - Initially considering the max timestamp in the store observation data as points of reference to define last hours, day or week.
     - After considering a particular period for calculation for a store, 
       finding the overlap between a period considered and the business hours.
     - If no overlap is found, then complete interval will be marked as downtime. 
     - Otherwise, Checking if there's a obervation during that duration, 
       if yes, then deciding the activity based on that observation
       Otherwise that duration will be considered as completely inactive or downtime.  
     - Using the crude logic to extrapolate the overlapping time interval, based on previous
       observation timestamp and current timestamp.    
    
    """
    
    def __init__(self):
        self.store_id_to_timezone_map = {timezone.store_id: timezone.timezone_str for timezone in list(StoreTimezone.objects.all())}
        """
        To avoid N+1 queries creating map for store_id to timezone.

        For same reason creating this map for store observation, it looks like {"store_id" : {"timestamp1": "status", "timestamp2": "status"}}
        """

        self.store_observation_map = {}

        for observation in list(StoreObservations.objects.all().order_by('timestamp_utc')):
            
            if self.store_observation_map.get(observation.store_id):
                self.store_observation_map[observation.store_id][observation.timestamp_utc] = observation.status
            
            self.store_observation_map[observation.store_id] = {observation.timestamp_utc : observation.status}


    def create_store_id_to_business_hours_map(self, store_business_hours_queryset : list[StoreBusinessHours]) -> dict:
        """
        This map will look like {"store_id": {"day_of_week": {"start_time": "end_time"}}}
        """
        print("Creating a map for store to weekwise business hours")
        
        store_id_to_business_hours_map = {}
        

        for business_hours in store_business_hours_queryset:

            if business_hours.store_id in store_id_to_business_hours_map:
                if business_hours.day_of_week in store_id_to_business_hours_map[business_hours.store_id]:
                    store_id_to_business_hours_map[business_hours.store_id][business_hours.day_of_week][business_hours.start_time_local] = business_hours.end_time_local
                else:
                    store_id_to_business_hours_map[business_hours.store_id][business_hours.day_of_week] = {business_hours.start_time_local: business_hours.end_time_local}
            else:
                store_id_to_business_hours_map[business_hours.store_id] = {business_hours.day_of_week: {business_hours.start_time_local: business_hours.end_time_local}}

        return store_id_to_business_hours_map
    

    def _calculate_overlap(self, period_start: datetime, period_end: datetime, business_hours: dict, store_id: str) -> int:
        """
        Calculate the overlap between a given period and business hours.
        Return the overlap in seconds.
        """
        period_start_local = period_start.time()
        period_end_local = period_end.time()

        if self.store_id_to_timezone_map.get(store_id):
            store_timezone = timezone(self.store_id_to_timezone_map[store_id])
            period_start_local = period_start.astimezone(store_timezone).time()
            period_end_local = period_end.astimezone(store_timezone).time()
        overlap = 0
        
        for business_start in business_hours:
            latest_start = max(period_start_local, business_start)
            earliest_end = min(period_end_local, business_hours[business_start])

            todays_date = datetime.now().date()
            earliest_end_datetime = datetime.combine(todays_date, earliest_end)
            latest_start_datetime = datetime.combine(todays_date, latest_start)
            
            delta = (earliest_end_datetime - latest_start_datetime).total_seconds()
            if delta > 0:
                overlap += delta
        return overlap

    def _calculate_uptime_downtime(self, store_id: str, period_start : datetime, period_end : datetime, business_hours: dict) -> tuple[int, int]:
        """
        Calculate the uptime and downtime for a store in a given period.
        """
        uptime = 0
        downtime = 0

        observation_within_period = {}

        if self.store_observation_map.get(store_id):
            for timestamp, status in self.store_observation_map[store_id].items():
                if period_start <= timestamp <= period_end:
                    observation_within_period[timestamp] = status

        
        last_status = False
        last_timestamp = period_start
      
        for observation_timestamp, status in observation_within_period.items():
           
            current_overlap = self._calculate_overlap(period_start = last_timestamp, period_end= observation_timestamp ,business_hours= business_hours, store_id= store_id)
            
            
            if last_status and current_overlap > 0:
                uptime += current_overlap

            else:
                downtime += (observation_timestamp - last_timestamp).total_seconds()
               
           
            last_status = status
            last_timestamp = observation_timestamp

       
        final_overlap = self._calculate_overlap(last_timestamp, period_end, business_hours, store_id)
        
        if last_status and final_overlap > 0:
            uptime += final_overlap
            
        else:
            downtime += (period_end - last_timestamp).total_seconds()
    
        return (uptime, downtime)

    
    def calculate_uptime_downtime_for_period(self, store_id: str, store_id_to_business_hours_map_in_utc : dict, period_end : datetime, period_start : datetime) -> tuple[int, int]:
        """
        Calculate the uptime and downtime for the given period.
        """
        
        business_hours_for_period = {}

        for day_of_week in store_id_to_business_hours_map_in_utc[store_id]:
            if period_start.weekday() <= day_of_week <= period_end.weekday():
                business_hours_for_period.update(store_id_to_business_hours_map_in_utc[store_id][day_of_week])
        
       
        (uptime, downtime) = self._calculate_uptime_downtime(
            store_id, period_start, period_end, business_hours_for_period
        )

        return (uptime, downtime)
       

    def calculate_uptime_downtime(self) -> list[dict]:

        uptime_downtime_data = []
        
        last_polled_timestamp = StoreObservations.objects.aggregate(last_poll_timestamp = Max("timestamp_utc"))['last_poll_timestamp']
      
        store_id_to_business_hours_map = self.create_store_id_to_business_hours_map(list(StoreBusinessHours.objects.all().order_by('day_of_week')))


        uptime = {"last_hour": 0, "last_day": 0, "last_week": 0}

        downtime = {"last_hour": 0, "last_day": 0, "last_week": 0}

        periods = {"last_hour" : last_polled_timestamp - timedelta(hours=1), "last_day" : last_polled_timestamp - timedelta(days = 1), "last_week": last_polled_timestamp - timedelta(weeks=1)}

        
        for store_id in store_id_to_business_hours_map:    
            for period in periods:
                
                print(f"Calculating uptime and downtime for {period} for store_id ={store_id}")
                (active_time, inactive_time) = self.calculate_uptime_downtime_for_period( store_id = store_id, store_id_to_business_hours_map_in_utc =store_id_to_business_hours_map, period_end=last_polled_timestamp, period_start=periods[period])
                
                uptime[period] = active_time
                downtime[period] = inactive_time

            uptime_downtime_data.append({"store_id": store_id, "last_hour_uptime" : round(uptime['last_hour']/60, 2), "last_hour_downtime": round(downtime['last_hour']/60, 2), "last_day_uptime": round(uptime["last_day"]/3600, 2), "last_day_downtime": round(downtime["last_day"]/3600, 2), "last_week_uptime": round(uptime["last_week"]/3600, 2), "last_week_downtime": round(downtime['last_week']/3600, 2)})    


        return uptime_downtime_data
        