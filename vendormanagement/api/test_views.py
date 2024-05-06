from django.test import TestCase
from django.urls import reverse
from datetime import datetime, timedelta
from rest_framework import status
from rest_framework.test import APITestCase
from base.models import Vendor, PurchaseOrder, HistoricalPerformance


class MyTestClass(TestCase):
    # Create your tests here.
    def test_acknowledge_purchase_order(self):
        """
        Tests successful acknowledgement of a purchase order.
        """

        # Create a vendor and purchase order
        vendor = Vendor.objects.create(name="Test Vendor", contact_details="Test_contact",
                                       address="Test_address",
                                       vendor_code="TestCode",
                                       on_time_delivery_rate=2.0,
                                       quality_rating_avg=2.0,
                                       average_response_time=3.0,
                                       fulfillment_rate=30.0)
        purchase_order = PurchaseOrder.objects.create(
            vendor=vendor, issue_date=datetime.now() - timedelta(days=2),  # Issued 2 days ago,
            order_date=datetime.now() - timedelta(days=3), delivery_date=datetime.now(),
            status="completed", items={"test_item1": 10, "test_item2": 20}, quantity=99, quality_rating=0,
        )

        # URL for the endpoint
        url = reverse('acknowledge_purchase_order', kwargs={'po_id': purchase_order.pk})

        # Send POST request
        response = self.client.post(url, {}, format='json')

        # Check response status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response message
        self.assertEqual(response.data['message'], 'Purchase order acknowledged successfully.')

        # Check if acknowledgment date is set
        purchase_order.refresh_from_db()  # Refresh purchase order object
        self.assertIsNotNone(purchase_order.acknowledgement_date)


class VendorOpsTest(APITestCase):

    def test_get_vendors(self):
        """
        Tests successful retrieval of all vendors through GET request.
        """

        # Create some vendor data
        Vendor.objects.create(name="Vendor 1", contact_details="Test_contact1",
                              address="Test_address1",
                              vendor_code="TestCode1", )
        Vendor.objects.create(name="Vendor 2", contact_details="Test_contact2",
                              address="Test_address2",
                              vendor_code="TestCode2", )

        url = reverse('vendor_ops')  # Assuming you have a URL pattern for vendor_ops

        # Send GET request
        response = self.client.get(url)

        # Check response status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data format (list of serialized vendor objects)
        self.assertEqual(len(response.data), 2)  # Expecting 2 vendors
        self.assertIsInstance(response.data[0], dict)  # Each item should be a dictionary

    def test_create_vendor(self):
        """
        Tests successful creation of a new vendor through POST request.
        """

        url = reverse('vendor_ops')

        # Valid vendor data
        data = {'name': 'New Vendor', 'contact_details': "Test_contact",
                'address': "Test_address",
                'vendor_code': "TestCode", }

        # Send POST request
        response = self.client.post(url, data, format='json')

        # Check response status code
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check response data (serialized newly created vendor)
        self.assertEqual(response.data['name'], 'New Vendor')

    def test_create_invalid_vendor(self):
        """
        Tests unsuccessful creation of a vendor with invalid data (missing name).
        """

        url = reverse('vendor_ops')

        # Invalid vendor data (missing name)
        data = {}

        # Send POST request
        response = self.client.post(url, data, format='json')

        # Check response status code
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Check response for expected error message (e.g., "This field is required.")
        self.assertIn('name', response.data)

    def test_method_not_allowed(self):
        """
        Tests response for unsupported HTTP methods (e.g., PUT, DELETE).
        """

        url = reverse('vendor_ops')

        # Unsupported methods (PUT, DELETE)
        methods = ['PUT', 'DELETE']

        for method in methods:
            response = self.client.generic(method, url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class GetVendorByIdTest(APITestCase):

    def setUp(self):
        """
        Creates a vendor object for testing.
        """
        self.vendor = Vendor.objects.create(name="Test Vendor")
        self.url = reverse('get_vendor_by_id', kwargs={'vendor_id': self.vendor.pk})

    def test_get_vendor(self):
        """
        Tests successful retrieval of a vendor by ID through GET request.
        """

        # Send GET request
        response = self.client.get(self.url)

        # Check response status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data (serialized vendor)
        self.assertEqual(response.data['name'], self.vendor.name)

    def test_get_nonexistent_vendor(self):
        """
        Tests response for a non-existent vendor through GET request.
        """

        # Non-existent vendor ID
        nonexistent_id = 100  # Assuming no vendor with this ID exists

        url = reverse('get_vendor_by_id', kwargs={'vendor_id': nonexistent_id})

        # Send GET request
        response = self.client.get(url)

        # Check response status code
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_vendor(self):
        """
        Tests successful update of a vendor through PUT request.
        """

        data = {'name': 'Updated Vendor'}

        # Send PUT request
        response = self.client.put(self.url, data, format='json')

        # Check response status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data (updated serialized vendor)
        self.assertEqual(response.data['name'], 'Updated Vendor')
        self.vendor.refresh_from_db()  # Refresh vendor object
        self.assertEqual(self.vendor.name, 'Updated Vendor')

    def test_update_vendor_invalid_data(self):
        """
        Tests unsuccessful update of a vendor with invalid data through PUT request.
        """

        data = {}  # Missing required field (e.g., name)

        # Send PUT request
        response = self.client.put(self.url, data, format='json')

        # Check response status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response for expected error message (e.g., "This field is required.")
        self.assertIn('name', response.data)

    def test_delete_vendor(self):
        """
        Tests successful deletion of a vendor through DELETE request.
        """

        # Send DELETE request
        response = self.client.delete(self.url)

        # Check response status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Attempt to retrieve the deleted vendor (should raise DoesNotExist)
        with self.assertRaises(Vendor.DoesNotExist):
            Vendor.objects.get(pk=self.vendor.pk)

    def test_method_not_allowed(self):
        """
        Tests response for unsupported HTTP methods (e.g., POST).
        """

        # Unsupported method (POST)
        method = 'POST'

        response = self.client.generic(method, self.url)

        # Check response status code
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class GetPOByIdTest(APITestCase):

    def setUp(self):
        self.vendor = Vendor.objects.create(name="Test Vendor")
        self.purchase_order = PurchaseOrder.objects.create(vendor=self.vendor,
                                                           order_date=datetime.now(),
                                                           delivery_date=datetime.now() + timedelta(days=1),
                                                           items={'test_item': 1},
                                                           quantity=1,
                                                           status='pending',
                                                           issue_date=datetime.now() + timedelta(days=1))
        self.url = reverse('get_po_by_id', kwargs={'po_id': self.purchase_order.pk})

    def test_get_purchase_order(self):
        """
        Tests successful retrieval of a purchase order by ID through GET request.
        """

        # Send GET request
        response = self.client.get(self.url)

        # Check response status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data (serialized purchase order)
        self.assertEqual(response.data['vendor'], self.vendor.pk)

    def test_get_nonexistent_purchase_order(self):
        """
        Tests response for a non-existent purchase order through GET request.
        """

        # Non-existent purchase order ID
        nonexistent_id = 100  # Assuming no purchase order with this ID exists

        url = reverse('get_po_by_id', kwargs={'po_id': nonexistent_id})

        # Send GET request
        response = self.client.get(url)

        # Check response status code
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GetVendorPerformanceTest(APITestCase):

    def setUp(self):
        self.vendor = Vendor.objects.create(name="Test Vendor")
        self.url = reverse('get_vendor_performance', kwargs={'vendor_id': self.vendor.pk})

    def test_get_performance_existing_vendor(self):
        """
        Tests successful retrieval of performance metrics for an existing vendor.
        """

        # Create some HistoricalPerformance data
        HistoricalPerformance.objects.create(
            vendor=self.vendor,
            date=datetime.now(),
            on_time_delivery_rate=0.9,
            quality_rating_avg=4.2,
            average_response_time=1.0,
            fulfillment_rate=0.8
        )

        # Send GET request
        response = self.client.get(self.url)

        # Check response status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data contains performance metrics
        self.assertEqual(response.data['on_time_delivery_rate'], 0.9)
        self.assertEqual(response.data['quality_rating_avg'], 4.2)
        self.assertEqual(response.data['average_response_time'], 1)  # Assuming conversion to hours
        self.assertEqual(response.data['fulfillment_rate'], 0.8)

    def test_get_performance_nonexistent_vendor(self):
        """
        Tests response for a non-existent vendor.
        """

        # Non-existent vendor ID
        nonexistent_id = 100

        url = reverse('get_vendor_performance', kwargs={'vendor_id': nonexistent_id})

        # Send GET request
        response = self.client.get(url)

        # Check response status code (404 Not Found)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Check response contains error message
        self.assertEqual(response.data['error'], 'Vendor not found.')

    def test_get_performance_no_data(self):
        """
        Tests response when no performance data exists for the vendor.
        """

        # Send GET request
        response = self.client.get(self.url)

        # Check response status code (200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response contains empty performance data
        self.assertEqual(response.data['on_time_delivery_rate'], 0.0)
        self.assertEqual(response.data['quality_rating_avg'], 0.0)
        self.assertEqual(response.data['average_response_time'], 0.0)
        self.assertEqual(response.data['fulfillment_rate'], 0.0)
