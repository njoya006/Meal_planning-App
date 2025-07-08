from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from api.serializers import ChefAssistantPromptSerializer
import os
import dotenv
from openai import OpenAI
import json
from django.core.cache import cache

# Load environment variables from a .env file if present, for local development and deployment best practices
dotenv.load_dotenv()

# Make sure to set your OpenAI API key in your environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Maximum conversation history to keep (in messages)
MAX_CONVERSATION_HISTORY = 10

class ChefAssistantView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ChefAssistantPromptSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        prompt = serializer.validated_data["prompt"]
        conversation_id = serializer.validated_data.get("conversation_id", None)
        
        # Get user preferences if available (from request.user if authenticated)
        user_preferences = {}
        if request.user and request.user.is_authenticated:
            try:
                # Try to get user profile or preferences if they exist in your model
                # This is a placeholder - adjust based on your actual user model structure
                if hasattr(request.user, 'profile'):
                    profile = request.user.profile
                    if hasattr(profile, 'dietary_preferences'):
                        user_preferences['dietary_preferences'] = profile.dietary_preferences
                    if hasattr(profile, 'favorite_cuisines'):
                        user_preferences['favorite_cuisines'] = profile.favorite_cuisines
                    if hasattr(profile, 'allergies'):
                        user_preferences['allergies'] = profile.allergies
            except Exception as e:
                # Just log the error but continue
                print(f"Error retrieving user preferences: {e}")
        
        if not conversation_id:
            # Generate a simple ID if none provided
            import uuid
            conversation_id = str(uuid.uuid4())
        
        # Retrieve conversation history from cache
        conversation_key = f"chef_conversation_{conversation_id}"
        conversation_history = cache.get(conversation_key, [])
        
        if not OPENAI_API_KEY:
            return Response({"error": "OpenAI API key not set."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            # Initialize the OpenAI client with the API key
            client = OpenAI(api_key=OPENAI_API_KEY)
            
            # Print debugging info to logs
            print("Using OpenAI API key:", OPENAI_API_KEY[:5] + "..." if OPENAI_API_KEY else "Not set")
            print(f"Making OpenAI API request for conversation {conversation_id} with prompt:", prompt)
            
            # Create a more intelligent system message
            system_message = {"role": "system", "content": """You are ChopSmo's intelligent Chef Assistant with the following capabilities:

1. PERSONALITY: Warm, friendly, and knowledgeable about food. Address users respectfully and conversationally.

2. CAMEROONIAN CUISINE EXPERTISE: You specialize in Cameroonian cuisine with deep knowledge of:
   - Traditional dishes (ndolé, eru, achu, poulet DG, koki, egusi pudding, kondre, mbongo tchobi, etc.)
   - Regional variations within Cameroon (highlighting differences between West, North, South, etc.)
   - Authentic ingredients, preparation techniques, and cultural significance of dishes
   - Substitutions for hard-to-find Cameroonian ingredients

3. RECIPE ASSISTANCE:
   - Provide detailed, step-by-step recipes when asked
   - Suggest cooking times and temperatures
   - Offer tips for preparation and presentation
   - Scale recipes up or down based on serving needs

4. INGREDIENT KNOWLEDGE:
   - Explain unfamiliar ingredients
   - Suggest seasonal alternatives
   - Provide nutritional information about foods
   - Help with food storage tips

5. COOKING TECHNIQUES:
   - Explain cooking methods (especially those specific to Cameroonian cuisine)
   - Troubleshoot cooking problems
   - Suggest kitchen tools and equipment

6. MEAL PLANNING:
   - Provide balanced meal suggestions
   - Recommend complementary dishes
   - Suggest menus for different occasions or dietary needs

7. DIETARY ACCOMMODATION:
   - Adapt recipes for different dietary needs (vegetarian, gluten-free, etc.)
   - Suggest healthier alternatives to traditional ingredients

8. CULTURAL CONTEXT:
   - Share the cultural significance of Cameroonian dishes
   - Explain traditional serving customs and pairings

When asked about non-Cameroonian cuisine, provide helpful information but also suggest a Cameroonian alternative with a brief explanation of why it might be enjoyable.

Only answer questions related to cooking, recipes, food, or ingredients. For other topics, politely reply: 'Sorry, I can only help with cooking and kitchen-related questions.'

Always make your responses practical, concise, and useful to home cooks.
"""}
            
            # Build the messages array with history and new prompt
            # Include user preferences if available
            augmented_prompt = prompt
            if user_preferences:
                preferences_str = ", ".join([f"{k}: {v}" for k, v in user_preferences.items()])
                augmented_prompt = f"[User preferences: {preferences_str}]\n\n{prompt}"
                
            messages = [system_message] + conversation_history + [{"role": "user", "content": augmented_prompt}]
            
            # Create a chat completion using the new client format with conversation history
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=250,
                temperature=0.7,
            )
            
            # Extract the response content from the new client format
            suggestion = response.choices[0].message.content.strip()
            print("Received response from OpenAI:", suggestion[:50] + "..." if len(suggestion) > 50 else suggestion)
            
            # Update conversation history with the new exchange
            conversation_history.append({"role": "user", "content": prompt})
            conversation_history.append({"role": "assistant", "content": suggestion})
            
            # Limit history size to avoid token limits
            if len(conversation_history) > MAX_CONVERSATION_HISTORY * 2:  # *2 because we count pairs of messages
                conversation_history = conversation_history[-MAX_CONVERSATION_HISTORY * 2:]
            
            # Save updated conversation history to cache (expire after 2 hours)
            cache.set(conversation_key, conversation_history, timeout=7200)
            
        except Exception as e:
            print("Chef Assistant error:", str(e))  # This will show the real error in the error log
            
            # Provide a helpful fallback based on common error types
            error_message = str(e).lower()
            if "rate limit" in error_message or "quota" in error_message:
                fallback_message = "I'm currently experiencing high demand. Please try again in a moment."
            elif "timeout" in error_message or "timed out" in error_message:
                fallback_message = "The request took too long to process. Please try a shorter question or try again later."
            elif "content policy" in error_message or "moderation" in error_message:
                fallback_message = "I can only help with cooking-related questions. Please ask something about food or recipes."
            elif "api key" in error_message or "authentication" in error_message:
                fallback_message = "There's a temporary issue with the chef service. The team has been notified."
                # You could add admin notification here
            else:
                fallback_message = "Sorry, I couldn't process your request. Please try asking in a different way or try again later."
                
            # If possible, suggest a related Cameroonian dish as a fallback
            common_queries = {
                "breakfast": "For breakfast ideas, you might enjoy Cameroonian beignets or puff-puff with beans.",
                "dinner": "For dinner recipes, popular Cameroonian dishes include ndolé with plantains or poulet DG.",
                "dessert": "For dessert, you might like Cameroonian sweet beignets or fried plantains with honey.",
                "drink": "Popular Cameroonian drinks include folere (hibiscus tea) or ginger juice.",
                "recipe": "I recommend trying a simple Cameroonian dish like poulet DG (Directeur Général chicken)."
            }
            
            # Check if the prompt contains any common query keywords
            for keyword, suggestion in common_queries.items():
                if keyword in prompt.lower():
                    fallback_message += f" {suggestion}"
                    break
            
            return Response({
                "suggestion": fallback_message,
                "conversation_id": conversation_id,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "suggestion": suggestion,
            "conversation_id": conversation_id
        }, status=status.HTTP_200_OK)
