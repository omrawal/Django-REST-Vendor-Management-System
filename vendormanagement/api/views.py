from rest_framework.response import Response
from rest_framework.decorators import api_view
from base.models import Vendor, PurchaseOrder, HistoricalPerformance
from .serializers import VendorSerializer, PurchaseOrderSerializer, HistoricalPerformanceSerializer
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
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET', 'PUT', 'DELETE'])
def get_vendor_by_id(request, vendor_id):
    if request.method == 'GET':
        try:
            vendor = Vendor.objects.get(pk=vendor_id)
        except Vendor.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = VendorSerializer(vendor)
        return Response(serializer.data)
    elif request.method == 'PUT':
        try:
            vendor = Vendor.objects.get(pk=vendor_id)
        except Vendor.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = VendorSerializer(vendor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        try:
            vendor = Vendor.objects.get(pk=vendor_id)
            vendor.delete()
            return Response({'message': 'Vendor deleted successfully.'})
        except Vendor.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


def update_on_time_delivery_rate(request_data):
    delivery_date = request_data['delivery_date']
    vendor_id = request_data['vendor']
    try:
        # Convert delivery_date string to a date object
        delivery_date = datetime.strptime(delivery_date, '%Y-%m-%d  %H:%M:%S')
    except ValueError:
        return Response({'error': 'Invalid delivery date format (YYYY-MM-DD HH:MM:SS expected).' + delivery_date},
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        # Filter completed POs for the vendor
        completed_pos = PurchaseOrder.objects.filter(status='completed', delivery_date__lte=delivery_date
                                                     ).count()

        # Count total completed POs for the vendor (regardless of delivery date)
        total_completed_pos = PurchaseOrder.objects.filter(vendor=vendor_id, status='completed').count()
        print('completed_pos', completed_pos)
        print('total_completed_pos', total_completed_pos)
        if total_completed_pos == 0:
            # No completed POs for the vendor, so completion rate is 0
            on_time_delivery_rate = 0.0
        else:
            on_time_delivery_rate = completed_pos / total_completed_pos

        return Response({'on_time_delivery_rate': on_time_delivery_rate}, status=status.HTTP_201_CREATED)

    except PurchaseOrder.DoesNotExist:
        return Response({'error': 'Vendor not found.'}, status=status.HTTP_404_NOT_FOUND)


def update_quality_rating(data):
    vendor = data['vendor']
    completed_pos = PurchaseOrder.objects.filter(vendor=vendor, status='completed')
    total_ratings = sum(po.quality_rating for po in completed_pos if po.quality_rating is not None)
    average_rating = total_ratings / len(completed_pos) if completed_pos else 0.0  # Handle division by zero
    return average_rating


def update_average_response_time(data):
    vendor = data['vendor']
    completed_pos = PurchaseOrder.objects.filter(vendor=vendor, acknowledgement_date__isnull=False)
    total_response_time = timedelta(seconds=0)
    for obj in completed_pos:
        total_response_time += (obj.acknowledgement_date - obj.issue_date)
    average_response_time = total_response_time / len(completed_pos) if completed_pos else timedelta(seconds=0)
    return average_response_time


def update_fulfillment_rate(data):
    vendor = data['vendor']
    completed_pos = PurchaseOrder.objects.filter(vendor=vendor, status='completed', issue_date__isnull=False)
    total_pos = PurchaseOrder.objects.filter(vendor=vendor)
    fulfilled_pos = len(completed_pos)
    fulfillment_rate = fulfilled_pos / len(total_pos) if total_pos else 0.0  # Handle division by zero
    return fulfillment_rate


@api_view(['GET', 'POST'])
def purchase_order_ops(request):
    if request.method == 'GET':
        purchase_orders = PurchaseOrder.objects.all()
        serializer = PurchaseOrderSerializer(purchase_orders, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = PurchaseOrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # TODO Performance metrics update
            # 1. on_time_delivery_rate
            print('request.data', request.data)
            on_time_delivery_rate = None
            quality_rating = None
            if request.data['status'].lower() == 'completed':
                update_on_time_delivery_rate_response = update_on_time_delivery_rate(request.data)
                if 'on_time_delivery_rate' not in update_on_time_delivery_rate_response.data:
                    print("on_time_delivery_rate NOT found", update_on_time_delivery_rate_response.data)
                    return update_on_time_delivery_rate_response
                else:
                    on_time_delivery_rate = update_on_time_delivery_rate_response.data['on_time_delivery_rate']
                    print('on_time_delivery_rate', on_time_delivery_rate)
                    vendor = Vendor.objects.get(pk=request.data['vendor'])
                    vendor.on_time_delivery_rate = on_time_delivery_rate
                    vendor.save()
                    # 2. quality_rating_avg
                    quality_rating = update_quality_rating(request.data)
                    print('quality_rating', quality_rating)
                    vendor = Vendor.objects.get(pk=request.data['vendor'])
                    vendor.quality_rating_avg = quality_rating
                    vendor.save()
            # 3. average_response_time
            average_response_time = update_average_response_time(request.data)
            print('average_response_time', average_response_time)
            vendor = Vendor.objects.get(pk=request.data['vendor'])
            vendor.average_response_time = average_response_time.total_seconds() / 3600
            vendor.save()
            # 4. fulfillment_rate
            fulfillment_rate = update_fulfillment_rate(request.data)
            print('fulfillment_rate', fulfillment_rate)
            vendor = Vendor.objects.get(pk=request.data['vendor'])
            vendor.fulfillment_rate = fulfillment_rate
            vendor.save()
            if all([on_time_delivery_rate, quality_rating, average_response_time, fulfillment_rate]):
                # Saving historical performance
                vendor = request.data['vendor']
                # Create and save the HistoricalPerformance object
                historical_performance = HistoricalPerformance.objects.create(
                    vendor=Vendor.objects.get(pk=request.data['vendor']),
                    date=datetime.now(),  # Use current date and time
                    on_time_delivery_rate=on_time_delivery_rate,
                    quality_rating_avg=quality_rating,
                    average_response_time=average_response_time.total_seconds() / 3600,  # Convert timedelta to hours
                    fulfillment_rate=fulfillment_rate
                )
                # Save the object (automatic on creation, but explicit for clarity)
                historical_performance.save()

            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET', 'PUT', 'DELETE'])
def get_po_by_id(request, po_id):
    if request.method == 'GET':
        try:
            purchase_order = PurchaseOrder.objects.get(pk=po_id)
        except PurchaseOrder.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = PurchaseOrderSerializer(purchase_order)
        return Response(serializer.data)
    elif request.method == 'PUT':
        try:
            purchase_order = PurchaseOrder.objects.get(pk=po_id)
        except PurchaseOrder.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = PurchaseOrderSerializer(purchase_order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            on_time_delivery_rate = None
            quality_rating = None
            if request.data['status'].lower() == 'completed':
                update_on_time_delivery_rate_response = update_on_time_delivery_rate(request.data)
                if 'on_time_delivery_rate' not in update_on_time_delivery_rate_response.data:
                    print("on_time_delivery_rate NOT found", update_on_time_delivery_rate_response.data)
                    return update_on_time_delivery_rate_response
                else:
                    on_time_delivery_rate = update_on_time_delivery_rate_response.data['on_time_delivery_rate']
                    print('on_time_delivery_rate', on_time_delivery_rate)
                    vendor = Vendor.objects.get(pk=request.data['vendor'])
                    vendor.on_time_delivery_rate = on_time_delivery_rate
                    vendor.save()
                    # 2. quality_rating_avg
                    quality_rating = update_quality_rating(request.data)
                    print('quality_rating', quality_rating)
                    vendor = Vendor.objects.get(pk=request.data['vendor'])
                    vendor.quality_rating_avg = quality_rating
                    vendor.save()
            # 3. average_response_time
            average_response_time = update_average_response_time(request.data)
            print('average_response_time', average_response_time)
            vendor = Vendor.objects.get(pk=request.data['vendor'])
            vendor.average_response_time = average_response_time.total_seconds() / 3600
            vendor.save()
            # 4. fulfillment_rate
            fulfillment_rate = update_fulfillment_rate(request.data)
            print('fulfillment_rate', fulfillment_rate)
            vendor = Vendor.objects.get(pk=request.data['vendor'])
            vendor.fulfillment_rate = fulfillment_rate
            vendor.save()
            if all([on_time_delivery_rate, quality_rating, average_response_time, fulfillment_rate]):
                # Saving historical performance
                vendor = request.data['vendor']
                # Create and save the HistoricalPerformance object
                historical_performance = HistoricalPerformance.objects.create(
                    vendor=Vendor.objects.get(pk=request.data['vendor']),
                    date=datetime.now(),  # Use current date and time
                    on_time_delivery_rate=on_time_delivery_rate,
                    quality_rating_avg=quality_rating,
                    average_response_time=average_response_time.total_seconds() / 3600,  # Convert timedelta to hours
                    fulfillment_rate=fulfillment_rate
                )
                # Save the object (automatic on creation, but explicit for clarity)
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
    try:
        # Retrieve the purchase order object
        purchase_order = PurchaseOrder.objects.get(pk=po_id)
    except PurchaseOrder.DoesNotExist:
        return Response({'error': 'Purchase order not found.'}, status=status.HTTP_404_NOT_FOUND)
    print(purchase_order)
    # if purchase_order.acknowledgement_date:
    #     return Response({'error': 'Purchase order already acknowledged.'}, status=status.HTTP_400_BAD_REQUEST)

        # Set acknowledgment date and save the purchase order
    purchase_order.acknowledgement_date = datetime.now()
    purchase_order.save()

    purchase_order_obj = {'vendor':purchase_order.vendor}
    # Update average response time
    # average_response_time
    average_response_time = update_average_response_time(purchase_order_obj)
    print('average_response_time', average_response_time)

    vendor = Vendor.objects.get(pk=purchase_order.vendor.id)
    vendor.average_response_time = average_response_time.total_seconds() / 3600
    vendor.save()


    # Return success response
    return Response({'message': 'Purchase order acknowledged successfully.'})
