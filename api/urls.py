from django.urls import path
from api.views.chef_assistant import ChefAssistantView

urlpatterns = [
    path("chef-assistant/", ChefAssistantView.as_view(), name="chef-assistant"),
]
