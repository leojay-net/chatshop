from django.urls import path, re_path
from .views import ChatView, ChatGetView

urlpatterns = [
    path('product-chat', ChatView.as_view(), name="product-chat"),
    re_path(r'^chats(?:/(?P<email>[^/]+))?(?:/(?P<session_key>[^/]+))?/?$', ChatGetView.as_view(), name='chat-get'),
]