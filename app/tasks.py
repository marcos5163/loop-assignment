from loop_assignment.celery import app as celery_app
from app.models import Report
from app.service.uptime_downtime_calculation import UptimeDowntimeCalculationService
import tempfile
import csv


@celery_app.task
def report_generation(report_id: str):
    report = Report.objects.filter(report_id=report_id, status=Report.INITIATED).first()

    for retry_count in range(3):
        report.status = Report.IN_PROCESS
        report.save()

        try:
            store_activity_data = UptimeDowntimeCalculationService().calculate_uptime_downtime()

            with tempfile.NamedTemporaryFile(delete=False, mode='w', newline='') as temp_csv_file:
                fieldnames = store_activity_data[0].keys()
                writer = csv.DictWriter(temp_csv_file, fieldnames=fieldnames)
                writer.writeheader()

                for row in store_activity_data:
                    writer.writerow(row)

            report.report_link = temp_csv_file.name
            report.status = Report.COMPLETED
            report.generation_retry_count = retry_count 
            report.save()

            # If the report generation was successful, exiting the retry loop.
            break

        except Exception as e:
            print(e)
        
            report.generation_retry_count = retry_count + 1
            report.save()

    else:
        # If the loop completes three retries without success, marking the report as failed.
        report.status = Report.FAILED
        report.save()
    

    

    
        


