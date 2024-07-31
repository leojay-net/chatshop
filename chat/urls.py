from django.urls import path, re_path
from .views import ChatView, ChatGetView

urlpatterns = [
    path('product-chat', ChatView.as_view(), name="product-chat"),
    path('chats/', ChatGetView.as_view(), name='chat-get-all'),
    path('chats/<str:email>/', ChatGetView.as_view(), name='chat-get-by-email'),
    path('chats/<email>/<str:session_key>/', ChatGetView.as_view(), name='chat-get-by-email-session'),
]