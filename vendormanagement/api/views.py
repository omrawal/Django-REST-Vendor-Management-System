from rest_framework.response import Response
from rest_framework.decorators import api_view
from base.models import Vendor, PurchaseOrder, HistoricalPerformance
from .serializers import VendorSerializer, PurchaseOrderSerializer, HistoricalPerformanceSerializer
from rest_framework import status


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


@api_view(['GET','PUT','DELETE'])
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

#