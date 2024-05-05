from django.db import models


# Create your models here.

class Vendor(models.Model):
    name = models.CharField(max_length=200)
    contact_details = models.TextField(max_length=200)
    address = models.TextField(max_length=200)
    vendor_code = models.CharField(max_length=100)
    on_time_delivery_rate = models.FloatField()
    quality_rating_avg = models.FloatField()
    average_response_time = models.FloatField()
    fulfillment_rate = models.FloatField()


class PurchaseOrder(models.Model):
    po_number = models.CharField(max_length=200)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    order_date = models.DateTimeField()
    delivery_date = models.DateTimeField()
    items = models.JSONField()
    quantity = models.IntegerField()
    status = models.CharField(max_length=20)
    quality_rating = models.FloatField()
    issue_date = models.DateTimeField()
    acknowledgement_date = models.DateTimeField()


class HistoricalPerformance(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    date = models.DateTimeField()
    on_time_delivery_rate = models.FloatField()
    quality_rating_avg = models.FloatField()
    average_response_time = models.FloatField()
    fulfillment_rate = models.FloatField()