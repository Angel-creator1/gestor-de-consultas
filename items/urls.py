from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = [
    path('items/', views.variable_list, name='itemList'),
    path('itemscreate/', csrf_exempt(views.variable_create), name='itemCreate'),
]