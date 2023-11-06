from django.test import TestCase
from app.models import Report
import uuid


class ReportGenerationTestCase(TestCase):
    
    def setUp(self) -> None:
        return super().setUp()
    
    def test_trigger_report_api(self):
        
        response = self.client.get("/trigger-report/")

        self.assertEqual(response.status_code , 200)
        
        report_queryset = Report.objects.all()

        self.assertEqual(len(report_queryset), 1)

        self.assertEqual(response.json()['report_id'], report_queryset.first().report_id)

        self.assertEqual(report_queryset.first().status, Report.INITIATED)

    def test_get_report_api(self):

        report = Report.objects.create(report_id= uuid.uuid4().hex, status = Report.IN_PROCESS)

        response = self.client.post("/get-report/", data={"report_id": report.report_id})

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.json(), {"report_status": Report.IN_PROCESS})
    


        
