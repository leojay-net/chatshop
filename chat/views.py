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
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            chat_history, created = self.get_or_create_chat_history(serializer.validated_data)
            user_input = serializer.validated_data.get('input', '')
            
            chat = self.model.start_chat(history=self.format_chat_history(chat_history.history or []))
            
            response = self.get_ai_response(chat, user_input, created)
            return self.process_ai_response(response, chat_history)
        except genai.types.generation_types.BlockedPromptException:
            return Response({"error": "The input was blocked due to safety concerns"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_or_create_chat_history(self, validated_data):
        email = validated_data['email']
        session_key = validated_data.get('session_key') or generate_unique_key()
        return ChatHistory.objects.get_or_create(email=email, session_key=session_key)

    def format_chat_history(self, history):
        formatted_history = []
        for message in history:
            if message['role'] == 'user':
                formatted_history.append({'parts': [{'text': message['parts'][0]['text']}]})
            elif message['role'] == 'model':
                formatted_history.append({'parts': [{'text': message['parts'][0]['text']}]})
        return formatted_history

    def get_ai_response(self, chat, user_input, is_new_session):
        sanitized_input = escape(user_input)
        if is_new_session:
            prompt = f"""
            User input: {sanitized_input}

            Instructions:
            1. Greet the user and ask what product they'd like to search for or purchase. Always stay in character as a product search assistant.
            2. If the input is about searching for or purchasing a product:
               a. If product details are provided, return them in JSON format with a key 'product' in curly braces where the details of the product is a sentence like this "I want to buy a gaming lapotp, 8gb ram 1tb" you would extract "gaming laptop, 8gb ram 1tb" or structure it more like a sentence and return in a json format like this "{{"product":"gaming laptop, 8gb ram 1tb"}}". this is an example.
            3. If the input is not about products, respond naturally while steering the conversation back to product search.
            4. Always stay in character as a product search assistant.

            Respond:
            """
        else:
            prompt = f"""
            User input: {sanitized_input}

            Instructions:
            1. If the input is about searching for or purchasing a product:
               a. If product details are provided, return them in JSON format with a key 'product' in curly braces where the details of the product is a sentence like this "I want to buy a gaming lapotp, 8gb ram 1tb" you would extract "gaming laptop, 8gb ram 1tb" or structure it more like a sentence and return in a json format like this "{{"product":"gaming laptop, 8gb ram 1tb"}}". this is an example.
            2. If the input is not about products, respond naturally while steering the conversation back to product search.
            3. Always stay in character as a product search assistant.

            Respond:
            """
        return chat.send_message(prompt)

    def process_ai_response(self, response, chat_history):
        try:
            product_json = self.extract_json(response.text)
            products = self.search_products(product_json['product'])
            return Response({'products': products}, status=status.HTTP_200_OK)
        except (ValueError, json.JSONDecodeError):
            self.update_chat_history(chat_history, response.text)
            return Response({
                'message': response.text,
                'session_key': chat_history.session_key
            }, status=status.HTTP_200_OK)

    def extract_json(self, text):
        json_start = text.index('{')
        json_end = text.rindex('}') + 1
        json_str = text[json_start:json_end]
        return json.loads(json_str)

    def search_products(self, product):
        searcher = MultiPlatformSearcher()
        sort_criteria = [('price', False), ('rating', True)]
        return searcher.search_and_sort_products(product, num_pages=3, sort_criteria=sort_criteria)

    def update_chat_history(self, chat_history, message):
        chat_history.history.append({'role': 'assistant', 'parts': [{'text': message}]})
        chat_history.save()
    

class ChatGetView(GenericAPIView):
    serializer_class = ChatHistorySerializer
    queryset = ChatHistory.objects.all()
    def get(self, request, id =None, email=None, session_key=None):
        try:
            if email and session_key:
                chat_history = ChatHistory.objects.get(email=email, session_key=session_key)
            elif email:
                chat_history = ChatHistory.objects.filter(email=email)
            elif session_key:
                chat_history = ChatHistory.objects.filter(session_key=session_key)
            else:
                chat_history = ChatHistory.objects.all()

            serializer = ChatHistorySerializer(chat_history, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response({"error": "Chat history not found"}, status=status.HTTP_404_NOT_FOUND)
        # except Exception as e:
        #     return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request,id =None, email=None, session_key=None):
        try:
            if email and session_key:
                chat_history = ChatHistory.objects.get(email=email, session_key=session_key)
                chat_history.delete()
            elif email:
                ChatHistory.objects.filter(email=email).delete()
            elif session_key:
                ChatHistory.objects.filter(session_key=session_key).delete()

            return Response({"message": "Chat history deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

        except ObjectDoesNotExist:
            return Response({"error": "Chat history not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, id =None, email=None, session_key=None):
        try:
            if email and session_key:
                chat_history = ChatHistory.objects.get(email=email, session_key=session_key)
            else:
                return Response({"error": "Both email and session_key are required for update"}, status=status.HTTP_400_BAD_REQUEST)

            serializer = ChatHistorySerializer(chat_history, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except ObjectDoesNotExist:
            return Response({"error": "Chat history not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)