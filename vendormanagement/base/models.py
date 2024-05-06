from django.db import models


# Create your models here.

class Vendor(models.Model):
    name = models.CharField(max_length=200)
    contact_details = models.TextField(max_length=200)
    address = models.TextField(max_length=200)
    vendor_code = models.CharField(max_length=100)
    on_time_delivery_rate = models.FloatField(null=True)
    quality_rating_avg = models.FloatField(null=True)
    average_response_time = models.FloatField(null=True)
    fulfillment_rate = models.FloatField(null=True)

    def __str__(self):
        """
        Returns a string representation of the Vendor object with all fields.
        """
        return f"Vendor(name='{self.name}', contact_details='{self.contact_details}', address='{self.address}', vendor_code='{self.vendor_code}', on_time_delivery_rate={self.on_time_delivery_rate}, quality_rating_avg={self.quality_rating_avg}, average_response_time={self.average_response_time}, fulfillment_rate={self.fulfillment_rate})"


class PurchaseOrder(models.Model):
    po_number = models.CharField(max_length=200)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    order_date = models.DateTimeField()
    delivery_date = models.DateTimeField()
    items = models.JSONField()
    quantity = models.IntegerField()
    status = models.CharField(max_length=20)
    quality_rating = models.FloatField(null=True)
    issue_date = models.DateTimeField()
    acknowledgement_date = models.DateTimeField(null=True)

    def __str__(self):
        # Include all fields in the string representation
        return f"""
    Purchase Order (pk: {self.pk})
      po_number: {self.po_number}
      vendor: {self.vendor}  # Use string representation of the vendor object
      order_date: {self.order_date}
      delivery_date: {self.delivery_date}
      items: {self.items}
      quantity: {self.quantity}
      status: {self.status}
      quality_rating: {self.quality_rating}
      issue_date: {self.issue_date}
      acknowledgement_date: {self.acknowledgement_date}
            """


class HistoricalPerformance(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    date = models.DateTimeField()
    on_time_delivery_rate = models.FloatField()
    quality_rating_avg = models.FloatField()
    average_response_time = models.FloatField()
    fulfillment_rate = models.FloatField()

    def __str__(self):
        """
        Returns a string representation of the HistoricalPerformance object
        including all fields.
        """
        return f"HistoricalPerformance(vendor={self.vendor}, date={self.date}, on_time_delivery_rate={self.on_time_delivery_rate}, quality_rating_avg={self.quality_rating_avg}, average_response_time={self.average_response_time}, fulfillment_rate={self.fulfillment_rate})"

