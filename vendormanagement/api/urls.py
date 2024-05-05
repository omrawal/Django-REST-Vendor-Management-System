from django.urls import path
from . import views

urlpatterns = [
    path('vendors', views.vendor_ops),
    path('vendors/<int:vendor_id>', views.get_vendor_by_id),
]