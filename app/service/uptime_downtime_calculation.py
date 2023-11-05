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
     - Then Checking if there's a obervation during that duration, 
       if yes, then deciding the activity based on that observation
       Otherwise that duration will be considered as completely inactive or downtime.  
     - Using the crude logic to extrapolate the overlapping time interval, based on previous
       observation timestamp and current timestamp.    
    
    """
    
    def __init__(self):
        pass

    def create_store_id_to_business_hours_map(self, store_business_hours_queryset):
        print("Converting business hours into UTC")
        
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
    

    def _calculate_overlap(self, period_start, period_end, business_hours, store_id):
        """
        Calculate the overlap between a given period and business hours.
        Return the overlap in seconds.
        """

        store_id_to_timezone_map = {timezone.store_id: timezone.timezone_str for timezone in StoreTimezone.objects.all()}

        store_timezone = timezone(store_id_to_timezone_map[store_id])
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

    def _calculate_uptime_downtime(self, store_id, period_start, period_end, business_hours):
        """
        Calculate the uptime and downtime for a store in a given period.
        """
        uptime = 0
        downtime = 0

       
        observations = StoreObservations.objects.filter(
            store_id=store_id,
            timestamp_utc__gte=period_start,
            timestamp_utc__lte=period_end
        ).order_by('timestamp_utc')

        
        last_status = 'inactive'
        last_timestamp = period_start

        for observation in observations:
           
            current_overlap = self._calculate_overlap(period_start = last_timestamp, period_end= observation.timestamp_utc,business_hours= business_hours, store_id= store_id)
            
            
            if last_status == 'active':
                uptime += current_overlap
            else:
                downtime += current_overlap
            
           
            last_status = observation.status
            last_timestamp = observation.timestamp_utc

        
        final_overlap = self._calculate_overlap(last_timestamp, period_end, business_hours, store_id)
        if last_status == 'active':
            uptime += final_overlap
        else:
            downtime += final_overlap

        return uptime, downtime

    
    def calculate_uptime_downtime_for_period(self, store_id, store_id_to_business_hours_map_in_utc, period_start, period_end):
        """
        Calculate the uptime and downtime for the given period.
        """
        
       
        business_hours_for_period = store_id_to_business_hours_map_in_utc.get(store_id, {}).get(period_start.weekday(), [])

       
        uptime, downtime = self._calculate_uptime_downtime(
            store_id, period_start, period_end, business_hours_for_period
        )

        return (uptime, downtime)
       

    def calculate_uptime_downtime(self) -> list[dict]:

        uptime_downtime_data = []
        
        last_polled_timestamp = StoreObservations.objects.aggregate(last_poll_timestamp = Max("timestamp_utc"))['last_poll_timestamp']
      
        store_id_to_business_hours_map_in_utc = self.create_store_id_to_business_hours_map(StoreBusinessHours.objects.all())


        uptime = {"last_hour": 0, "last_day": 0, "last_week": 0}

        downtime = {"last_hour": 0, "last_day": 0, "last_week": 0}

        periods = {"last_hour" : last_polled_timestamp - timedelta(hours=1), "last_day" : last_polled_timestamp - timedelta(days = 1), "last_week": last_polled_timestamp - timedelta(weeks=1)}

        
        for store_id in store_id_to_business_hours_map_in_utc:     
            for period in periods:
                
                print(f"Calculating uptime and downtime for {period} for store_id ={store_id}")
                (active_time, inactive_time) = self.calculate_uptime_downtime_for_period( store_id = store_id, store_id_to_business_hours_map_in_utc =store_id_to_business_hours_map_in_utc, period_end=last_polled_timestamp, period_start=periods[period])
                
                uptime[period] = active_time
                downtime[period] = inactive_time

            uptime_downtime_data.append({"store_id": store_id, "last_hour_uptime" : uptime['last_hour'], "last_hour_downtime": downtime['last_hour'], "last_day_uptime": uptime["last_day"], "last_day_downtime": downtime["last_day"], "last_week_uptime": uptime["last_week"], "last_week_downtime": downtime['last_week']})    


        return uptime_downtime_data
        