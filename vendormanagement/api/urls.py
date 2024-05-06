from django.urls import path
from . import views

urlpatterns = [
    path('vendors', views.vendor_ops),
    path('vendors/<int:vendor_id>', views.get_vendor_by_id),
    path('purchase_orders', views.purchase_order_ops),
    path('purchase_orders/<int:po_id>', views.get_po_by_id),
    path('purchase_orders/<int:po_id>/acknowledge', views.acknowledge_purchase_order),
    path('vendors/<int:vendor_id>/performance/', views.get_vendor_performance),
]