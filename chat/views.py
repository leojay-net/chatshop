import json
from django.conf import settings
import google.generativeai as genai
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from .models import ChatHistory
from .serializers import ChatHistorySerializer
from django.core.exceptions import ObjectDoesNotExist
from .utils.key import generate_unique_key
from .utils.products import MultiPlatformSearcher
import os
from dotenv import load_dotenv
from django.utils.html import escape

load_dotenv()

class ChatView(GenericAPIView):
    serializer_class = ChatHistorySerializer
    queryset = ChatHistory.objects.all()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def post(self, request, format=None):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            # print(1)
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # print('a')
            chat_history, created = self.get_or_create_chat_history(serializer.validated_data)
            # print('b')
            user_input = serializer.validated_data.get('input', '')
            # print('c')
            
            # Save user input to chat history
            # print(2)
            self.update_chat_history(chat_history, user_input, 'user')
            # print(3)

            chat = self.model.start_chat(history=self.format_chat_history(chat_history.history or []))
            # print('d')
            
            response = self.get_ai_response(chat, user_input, created)
            # print('e')
            return self.process_ai_response(response, chat_history)
        except genai.types.generation_types.BlockedPromptException:
            return Response({"error": "The input was blocked due to safety concerns"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # print(e)
            # print(4)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_or_create_chat_history(self, validated_data):
        email = validated_data['email']
        session_key = validated_data.get('session_key') or generate_unique_key()
        return ChatHistory.objects.get_or_create(email=email, session_key=session_key)

    def format_chat_history(self, history):
        formatted_history = []
        for message in history:
            formatted_history.append({'parts': [{'text': message['parts'][0]['text']}], 'role': message['role']})
        return formatted_history

    def get_ai_response(self, chat, user_input, is_new_session):
        sanitized_input = escape(user_input)
        
        if is_new_session:
            prompt = f"""
            You are ChatShop, an AI assistant for product searches. Your goal is to quickly gather key product details and return them in JSON format.

            User input: {sanitized_input}

            Instructions:
            1. Greet the user and ask what product they're looking for.
            2. Ask up to 2 follow-up questions to get essential details.
            3. After 3 total interactions (including the initial query), provide the product details in this JSON format: {{"product": "detailed product description"}}
            4. Translate vague terms into specific, searchable ones.
            5. Stay focused on getting product search details.

            Example:
            Assistant: Hi! I'm ChatShop. What product are you searching for?
            User: A laptop
            Assistant: What type of laptop? (e.g., gaming, work, general use)
            User: A gaming laptop
            Assistant: Got it. What's your preferred RAM and storage?
            User: 8GB RAM and 500GB storage
            Assistant: Thanks. Here's what I've gathered:
            {{"product": "gaming laptop 8GB RAM 500GB storage"}}

            Respond:
            """
        else:
            prompt = f"""
            Continue as ChatShop, quickly gathering product details. Remember:

            1. Ask no more than 2 follow-up questions.
            2. Provide product details in JSON format after 3 total interactions.
            3. Format: {{"product": "detailed product description"}}
            4. Use specific, searchable terms.

            User input: {sanitized_input}

            Respond:
            """
        
        return chat.send_message(prompt)

    def process_ai_response(self, response, chat_history):
        try:
            product_json = self.extract_json(response.text)
            products = self.search_products(product_json['product'])
            
            # Save AI response to chat history
            # print(5)
            self.update_chat_history(chat_history, response.text, 'model')
            # print(6)
            try:
                j = response.text.rindex('}') + 1
                text = response.text[j:]
            except: 
                text = response.text
            return Response({
                'products': products,
                'message': text,
                'session_key': chat_history.session_key
            }, status=status.HTTP_200_OK)
        except (ValueError, json.JSONDecodeError):
            # Save AI response to chat history
            # print(7)
            self.update_chat_history(chat_history, response.text, 'model')
            # print(8)

            return Response({
                'message': response.text,
                'session_key': chat_history.session_key
            }, status=status.HTTP_200_OK)

    def extract_json(self, text):
        json_start = text.index('{')
        json_end = text.rindex('}') + 1
        json_str = text[json_start:json_end]
        print("Products",json_str)
        return json.loads(json_str)

    def search_products(self, product):
        searcher = MultiPlatformSearcher()
        sort_criteria = [('price', False), ('rating', True)]
        return searcher.search_and_sort_products(product, num_pages=3, sort_criteria=sort_criteria)

    def update_chat_history(self, chat_history, message, role):
        chat_history.history.append({'role': role, 'parts': [{'text': message}]})
        chat_history.save()

class ChatGetView(GenericAPIView):
    serializer_class = ChatHistorySerializer
    queryset = ChatHistory.objects.all()

    def get(self, request, id=None, email=None, session_key=None):
        try:
            if email and session_key:
                chat_history = ChatHistory.objects.filter(email=email, session_key=session_key)
            elif email:
                chat_history = ChatHistory.objects.filter(email=email)
            elif session_key:
                chat_history = ChatHistory.objects.filter(session_key=session_key)
            else:
                chat_history = ChatHistory.objects.all()

            serializer = ChatHistorySerializer(chat_history, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            # print(9)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, id=None, email=None, session_key=None):
        try:
            if email and session_key:
                chat_history = ChatHistory.objects.filter(email=email, session_key=session_key)
            elif email:
                chat_history = ChatHistory.objects.filter(email=email)
            elif session_key:
                chat_history = ChatHistory.objects.filter(session_key=session_key)
            else:
                return Response({"error": "Email or session_key is required for deletion"}, status=status.HTTP_400_BAD_REQUEST)

            if not chat_history.exists():
                return Response({"error": "Chat history not found"}, status=status.HTTP_404_NOT_FOUND)

            chat_history.delete()
            return Response({"message": "Chat history deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            # print(10)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, id=None, email=None, session_key=None):
        try:
            if not (email and session_key):
                return Response({"error": "Both email and session_key are required for update"}, status=status.HTTP_400_BAD_REQUEST)

            chat_history = ChatHistory.objects.filter(email=email, session_key=session_key).first()
            if not chat_history:
                return Response({"error": "Chat history not found"}, status=status.HTTP_404_NOT_FOUND)

            serializer = ChatHistorySerializer(chat_history, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            # print(11)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # print(12)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)