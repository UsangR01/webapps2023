from django.urls import path
from . import views

urlpatterns = [
    path('webapps2023/', views.home, name='home'),
    path('summary/', views.summary, name="dashboard"),
    path('help/', views.help, name='help'),
    path('contact/', views.contact, name='contact'),
    path('generate_plot/', views.generate_plot, name='generate_plot'),
]