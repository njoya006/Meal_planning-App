from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from api.serializers import ChefAssistantPromptSerializer
import os
import dotenv
from openai import OpenAI

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
            # Initialize the OpenAI client with the API key
            client = OpenAI(api_key=OPENAI_API_KEY)
            
            # Print debugging info to logs
            print("Using OpenAI API key:", OPENAI_API_KEY[:5] + "..." if OPENAI_API_KEY else "Not set")
            print("Making OpenAI API request with prompt:", prompt)
            
            # Create a chat completion using the new client format
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a warm and friendly chef assistant specializing in Cameroonian cuisine. Respond politely to greetings (like 'hello', 'hi', 'good morning', etc.) with appropriate warm greetings and introduce yourself as ChopSmo's Chef Assistant. When asked about food, recipes, or cooking tips, prioritize Cameroonian dishes and ingredients (such as ndolé, eru, achu, poulet DG, koki, egusi pudding, kondre, mbongo tchobi, etc.). If the user asks about food from other cuisines, still provide help but gently recommend a Cameroonian alternative too. Only answer questions related to cooking, recipes, kitchen tips, food, or ingredients. For other topics, politely reply: 'Sorry, I can only help with cooking and kitchen-related questions.'"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.7,
            )
            
            # Extract the response content from the new client format
            suggestion = response.choices[0].message.content.strip()
            print("Received response from OpenAI:", suggestion[:50] + "..." if len(suggestion) > 50 else suggestion)
        except Exception as e:
            print("Chef Assistant error:", str(e))  # This will show the real error in the error log
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"suggestion": suggestion}, status=status.HTTP_200_OK)
