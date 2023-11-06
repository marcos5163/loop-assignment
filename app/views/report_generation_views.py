from rest_framework.viewsets import ViewSet
import uuid
from app.models import Report
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from app.tasks import report_generation


class ReportGenerationViewSet(ViewSet):
    
    def trigger_report_generation(self, request):
        
        report_id = uuid.uuid4().hex
        report = Report.objects.create(report_id = report_id, status = Report.INITIATED)

        report_generation.delay(report.report_id)

        return Response(status=HTTP_200_OK, data={"report_id": report_id})
        

    def report_generation_status(self, request):
        
        report_id = request.data.get("report_id")

        if report_id is None:
            return Response(status= HTTP_400_BAD_REQUEST, data = {"error":"Report id not provided"})
        
        report = Report.objects.filter(report_id = report_id).first()

        if report is None:
            return Response(status=HTTP_400_BAD_REQUEST, data = {"error": "Invalid report id"})
        
        
        if report.status == Report.COMPLETED:
           
            report_file_path = report.report_link
            
            with open(report_file_path, 'r') as file:
                report_data = file.read()

            response = Response(report_data, headers={'content-type': 'text/csv'})

            response['Content-Disposition'] = 'attachment; filename="store_monitoring_report.csv"'  

            return response
        
        return Response(status=HTTP_200_OK, data={"report_status": report.status})