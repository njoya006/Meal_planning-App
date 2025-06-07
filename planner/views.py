# planner/views.py

from rest_framework import viewsets, permissions
from .models import MealPlan, NutritionInfo
from .serializers import MealPlanSerializer, NutritionInfoSerializer
from .permissions import IsVerifiedContributor
from rest_framework import serializers

class MealPlanViewSet(viewsets.ModelViewSet):
    serializer_class = MealPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return meal plans for the current user
        return MealPlan.objects.filter(user=self.request.user).order_by('date')

    def perform_create(self, serializer):
        # Automatically set the user to the current user
        serializer.save(user=self.request.user)

class NutritionInfoViewSet(viewsets.ModelViewSet):
    queryset = NutritionInfo.objects.all()
    serializer_class = NutritionInfoSerializer
    permission_classes = [IsVerifiedContributor]

    def perform_create(self, serializer):
        # Ensure nutrition is only added once per recipe
        if NutritionInfo.objects.filter(recipe=serializer.validated_data['recipe']).exists():
            raise serializers.ValidationError("Nutrition info for this recipe already exists.")
        serializer.save()

