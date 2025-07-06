from rest_framework import serializers

class ChefAssistantPromptSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=500)
