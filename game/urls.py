# game/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views  # Import auth_views correctly
from . import views

urlpatterns = [
    path('', views.newspaper_view, name='newspaper'),
    path('select/', views.stock_selection_view, name='stock_selection'),
    path('results/', views.results_view, name='results'),
]
