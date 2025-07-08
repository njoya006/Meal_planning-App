from rest_framework import serializers

class ChefAssistantPromptSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=500)
    conversation_id = serializers.CharField(max_length=100, required=False)
