from django.urls import path

from .views import CentreListView

urlpatterns = [
    path('', CentreListView.as_view(), name='centre-list'),
]
