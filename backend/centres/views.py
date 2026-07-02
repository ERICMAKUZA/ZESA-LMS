from rest_framework import generics, permissions
from rest_framework import serializers as drf_serializers

from .models import Centre


class CentreSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = Centre
        fields = ('id', 'name', 'is_primary', 'location')


class CentreListView(generics.ListAPIView):
    serializer_class = CentreSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Centre.objects.all()
    pagination_class = None
