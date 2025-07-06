from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from api.serializers import ChefAssistantPromptSerializer
import openai
import os
import dotenv

# Load environment variables from a .env file if present, for local development and deployment best practices
dotenv.load_dotenv()

# Make sure to set your OpenAI API key in your environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class ChefAssistantView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ChefAssistantPromptSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        prompt = serializer.validated_data["prompt"]

        if not OPENAI_API_KEY:
            return Response({"error": "OpenAI API key not set."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            openai.api_key = OPENAI_API_KEY
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert chef assistant. Only answer questions related to cooking, recipes, kitchen tips, food, or ingredients. If the user asks about anything else, politely reply: 'Sorry, I can only help with cooking and kitchen-related questions.'"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7,
            )
            suggestion = response.choices[0].message["content"].strip()
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"suggestion": suggestion}, status=status.HTTP_200_OK)
