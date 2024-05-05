from base.models import Vendor,PurchaseOrder,HistoricalPerformance

Vendor.objects.create(name='vendor1', contact_details='vendor1_contact', address='vendor1_address', vendor_code='v1',
                      on_time_delivery_rate=1.0, quality_rating_avg=1.0, average_response_time=1.0,fulfillment_rate=10.0)