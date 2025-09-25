from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = [
    path('items/', views.item_list, name='itemList'),
    path('itemcreate/', csrf_exempt(views.item_create), name='itemCreate'),
]