from rest_framework.response import Response
from rest_framework.decorators import api_view
from base.models import Vendor, PurchaseOrder, HistoricalPerformance
from .serializers import (
    VendorSerializer,
    PurchaseOrderSerializer,
    HistoricalPerformanceSerializer,
)
from rest_framework import status
from datetime import datetime, timedelta


@api_view(['GET', 'POST'])
def vendor_ops(request):
    if request.method == 'GET':
        vendors = Vendor.objects.all()
        serializer = VendorSerializer(vendors, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = VendorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET', 'PUT', 'DELETE'])
def get_vendor_by_id(request, vendor_id):
    """
        Retrieves, updates, or deletes a vendor based on the provided ID.

        Args:
            request: The incoming HTTP request.
            vendor_id: The unique identifier of the vendor.

        Returns:
            A JSON response with the vendor data, error message, or success message
            depending on the request method and outcome.
    """

    try:
        vendor = Vendor.objects.get(pk=vendor_id)
    except Vendor.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = VendorSerializer(vendor)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = VendorSerializer(vendor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        vendor.delete()
        return Response({'message': 'Vendor deleted successfully.'})
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


def update_on_time_delivery_rate(request_data):
    """
        Calculates and updates the on-time delivery rate for a vendor based on a provided delivery date.

        Args:
            request_data (dict): Dictionary containing delivery date and vendor ID.

        Returns:
            Response: JSON response with the calculated on-time delivery rate or an error message.
    """
    delivery_date_str = None
    try:
        # Validate and convert delivery date format
        delivery_date_str = request_data['delivery_date']
        delivery_date = datetime.strptime(delivery_date_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return Response(
            {'error': f'Invalid delivery date format (YYYY-MM-DD HH:MM:SS expected): {delivery_date_str}'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        vendor_id = request_data['vendor']
        # Filter completed POs for the vendor
        completed_pos = PurchaseOrder.objects.filter(status='completed', delivery_date__lte=delivery_date
                                                     ).count()

        # Count total completed POs for the vendor (regardless of delivery date)
        total_completed_pos = PurchaseOrder.objects.filter(vendor=vendor_id, status='completed').count()

        if total_completed_pos == 0:
            # No completed POs for the vendor, so completion rate is 0
            on_time_delivery_rate = 0.0
        else:
            on_time_delivery_rate = completed_pos / total_completed_pos

        return Response({'on_time_delivery_rate': on_time_delivery_rate}, status=status.HTTP_201_CREATED)

    except PurchaseOrder.DoesNotExist:
        return Response({'error': 'Vendor not found.'}, status=status.HTTP_404_NOT_FOUND)


def update_quality_rating(data):
    """
        Calculates the average quality rating for a vendor based on completed purchase orders.

        Args:
            data (dict): Dictionary containing vendor information. (Expected to have a 'vendor' key)

        Returns:
            float: The average quality rating for the vendor (0.0 if no completed purchase orders).
    """
    vendor = data['vendor']
    completed_pos = PurchaseOrder.objects.filter(vendor=vendor, status='completed')

    # Count only non-None quality ratings for accurate average calculation
    total_ratings = sum(po.quality_rating for po in completed_pos if po.quality_rating is not None)

    # Handle division by zero gracefully
    average_rating = total_ratings / len(completed_pos) if completed_pos else 0.0

    return average_rating


def update_average_response_time(data):
    """
        Calculates the average response time for a vendor based on purchase order data.

        Args:
            data (dict): A dictionary containing vendor information.

        Returns:
            datetime.timedelta: The average response time for the vendor.
    """

    vendor = data['vendor']
    completed_pos = PurchaseOrder.objects.filter(vendor=vendor, acknowledgement_date__isnull=False)
    total_response_time = timedelta(seconds=0)

    for obj in completed_pos:
        total_response_time += (obj.acknowledgement_date - obj.issue_date)
    average_response_time = total_response_time / len(completed_pos) if completed_pos else timedelta(seconds=0)
    return average_response_time


def update_fulfillment_rate(data):
    """
        Calculates the fulfillment rate for a vendor based on purchase order data.

        Args:
            data (dict): A dictionary containing vendor information, potentially
                including a 'vendor' key.

        Returns:
            float: The calculated fulfillment rate (0.0 to 1.0).
    """
    vendor = data.get('vendor')
    if not vendor:
        return 0.0  # Handle missing vendor information

    completed_pos = PurchaseOrder.objects.filter(
        vendor=vendor, status='completed', issue_date__isnull=False
    )
    total_pos = PurchaseOrder.objects.filter(vendor=vendor)

    fulfilled_pos = len(completed_pos)
    fulfillment_rate = fulfilled_pos / len(total_pos) if total_pos else 0.0  # Handle division by zero

    return fulfillment_rate


@api_view(['GET', 'POST'])
def purchase_order_ops(request):
    """
        Handles GET and POST requests for Purchase Orders.

        - GET: Retrieves all purchase orders.
        - POST: Creates a new purchase order and updates vendor performance metrics.
    """
    if request.method == 'GET':
        purchase_orders = PurchaseOrder.objects.all()
        serializer = PurchaseOrderSerializer(purchase_orders, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = PurchaseOrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            # Performance metrics update
            # 1. on_time_delivery_rate
            on_time_delivery_rate = None
            quality_rating = None
            average_response_time = None
            fulfillment_rate = None

            if request.data['status'].lower() == 'completed':
                update_on_time_delivery_rate_response = update_on_time_delivery_rate(request.data)
                if 'on_time_delivery_rate' not in update_on_time_delivery_rate_response.data:
                    return update_on_time_delivery_rate_response
                else:
                    on_time_delivery_rate = update_on_time_delivery_rate_response.data['on_time_delivery_rate']
                    vendor = Vendor.objects.get(pk=request.data['vendor'])
                    vendor.on_time_delivery_rate = on_time_delivery_rate
                    vendor.save()

                quality_rating = update_quality_rating(request.data)
                vendor = Vendor.objects.get(pk=request.data['vendor'])
                vendor.quality_rating_avg = quality_rating
                vendor.save()

            # 3. average_response_time
            average_response_time = update_average_response_time(request.data)
            vendor = Vendor.objects.get(pk=request.data['vendor'])
            vendor.average_response_time = average_response_time.total_seconds() / 3600
            vendor.save()

            # 4. fulfillment_rate
            fulfillment_rate = update_fulfillment_rate(request.data)
            vendor = Vendor.objects.get(pk=request.data['vendor'])
            vendor.fulfillment_rate = fulfillment_rate
            vendor.save()

            if all([on_time_delivery_rate, quality_rating, average_response_time, fulfillment_rate]):
                # Create and save the HistoricalPerformance object
                historical_performance = HistoricalPerformance.objects.create(
                    vendor=Vendor.objects.get(pk=request.data['vendor']),
                    date=datetime.now(),  # Use current date and time
                    on_time_delivery_rate=on_time_delivery_rate,
                    quality_rating_avg=quality_rating,
                    average_response_time=average_response_time.total_seconds() / 3600,  # Convert timedelta to hours
                    fulfillment_rate=fulfillment_rate
                )
                historical_performance.save()

            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET', 'PUT', 'DELETE'])
def get_po_by_id(request, po_id):
    """
        Retrieve, update, or delete a purchase order by its ID.

        - GET: Retrieves a purchase order.
        - PUT: Updates a purchase order.
        - DELETE: Deletes a purchase order.
    """
    purchase_order = None
    try:
        purchase_order = PurchaseOrder.objects.get(pk=po_id)
    except PurchaseOrder.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = PurchaseOrderSerializer(purchase_order)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = PurchaseOrderSerializer(purchase_order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # Performance metrics update
            # 1. on_time_delivery_rate
            on_time_delivery_rate = None
            quality_rating = None
            average_response_time = None
            fulfillment_rate = None

            if request.data['status'].lower() == 'completed':
                update_on_time_delivery_rate_response = update_on_time_delivery_rate(request.data)
                if 'on_time_delivery_rate' not in update_on_time_delivery_rate_response.data:
                    return update_on_time_delivery_rate_response
                else:
                    on_time_delivery_rate = update_on_time_delivery_rate_response.data['on_time_delivery_rate']
                    vendor = Vendor.objects.get(pk=request.data['vendor'])
                    vendor.on_time_delivery_rate = on_time_delivery_rate
                    vendor.save()

                quality_rating = update_quality_rating(request.data)
                vendor = Vendor.objects.get(pk=request.data['vendor'])
                vendor.quality_rating_avg = quality_rating
                vendor.save()

            # 3. average_response_time
            average_response_time = update_average_response_time(request.data)
            vendor = Vendor.objects.get(pk=request.data['vendor'])
            vendor.average_response_time = average_response_time.total_seconds() / 3600
            vendor.save()

            # 4. fulfillment_rate
            fulfillment_rate = update_fulfillment_rate(request.data)
            vendor = Vendor.objects.get(pk=request.data['vendor'])
            vendor.fulfillment_rate = fulfillment_rate
            vendor.save()

            if all([on_time_delivery_rate, quality_rating, average_response_time, fulfillment_rate]):
                # Create and save the HistoricalPerformance object
                historical_performance = HistoricalPerformance.objects.create(
                    vendor=Vendor.objects.get(pk=request.data['vendor']),
                    date=datetime.now(),  # Use current date and time
                    on_time_delivery_rate=on_time_delivery_rate,
                    quality_rating_avg=quality_rating,
                    average_response_time=average_response_time.total_seconds() / 3600,  # Convert timedelta to hours
                    fulfillment_rate=fulfillment_rate
                )
                historical_performance.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        try:
            purchase_order = PurchaseOrder.objects.get(pk=po_id)
            purchase_order.delete()
            return Response({'message': 'Purchase Order deleted successfully.'})
        except PurchaseOrder.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
def get_vendor_performance(request, vendor_id):
    """
        Retrieves the historical performance metrics for a specific vendor.

        URL Parameters:
            vendor_id: The unique identifier of the vendor.

        Returns:
            A JSON response with the performance metrics (on_time_delivery_rate,
            quality_rating_avg, average_response_time, fulfillment_rate) or an
            error message if the vendor is not found.
    """
    try:
        # Retrieve the vendor object
        vendor = Vendor.objects.get(pk=vendor_id)
    except Vendor.DoesNotExist:
        return Response({'error': 'Vendor not found.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        # Get the most recent HistoricalPerformance object for the vendor
        performance = HistoricalPerformance.objects.filter(vendor=vendor).order_by('-date').first()

        if not performance:
            # No performance data available yet, return empty response
            return Response({
                'on_time_delivery_rate': 0.0,
                'quality_rating_avg': 0.0,
                'average_response_time': 0.0,
                'fulfillment_rate': 0.0,
            })

        # Extract and return performance data
        return Response({
            'on_time_delivery_rate': performance.on_time_delivery_rate,
            'quality_rating_avg': performance.quality_rating_avg,
            'average_response_time': performance.average_response_time,
            'fulfillment_rate': performance.fulfillment_rate,
        })

    except HistoricalPerformance.DoesNotExist:
        # No performance data available yet, return empty response
        return Response({
            'on_time_delivery_rate': 0.0,
            'quality_rating_avg': 0.0,
            'average_response_time': 0.0,
            'fulfillment_rate': 0.0,
        })


@api_view(['POST'])
def acknowledge_purchase_order(request, po_id):
    """
        Acknowledges a purchase order by the vendor.

        URL Parameters:
            po_id (int): The unique identifier of the purchase order.

        Returns:
            Response: A JSON response with a success message or an error message.
    """
    try:
        # Retrieve the purchase order object
        purchase_order = PurchaseOrder.objects.get(pk=po_id)
    except PurchaseOrder.DoesNotExist:
        return Response({'error': 'Purchase order not found.'}, status=status.HTTP_404_NOT_FOUND)

    # if purchase_order.acknowledgement_date:
    #     return Response({'error': 'Purchase order already acknowledged.'}, status=status.HTTP_400_BAD_REQUEST)

    # Set acknowledgment date and save the purchase order
    purchase_order.acknowledgement_date = datetime.now()
    purchase_order.save()

    # Update average response time
    purchase_order_obj = {'vendor': purchase_order.vendor}
    average_response_time = update_average_response_time(purchase_order_obj)

    # Update vendor average response time
    vendor = Vendor.objects.get(pk=purchase_order.vendor.id)
    vendor.average_response_time = average_response_time.total_seconds() / 3600
    vendor.save()

    # Return success response
    return Response({'message': 'Purchase order acknowledged successfully.'})
