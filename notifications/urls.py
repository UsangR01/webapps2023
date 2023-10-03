from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path("notification_list/", views.notification_list, name="notification_list"),
    path("notification_mark_read/<int:notification_id>", views.notification_mark_read, name="notification_mark_read"),
    path("notification_delete/<int:notification_id>", views.notification_delete, name="notification_delete"),
    path('notifications/delete-multiple/', views.notification_delete_multiple, name='notification_delete_multiple'),

]



