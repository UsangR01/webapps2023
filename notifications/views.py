from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.shortcuts import redirect

from .models import Notification

@login_required
def notification_list(request):
    notifications = list(Notification.objects.filter(recipient=request.user).order_by('-timestamp'))
    context = {'notifications': notifications}
    return render(request, 'notifications/notification_list.html', context)


@login_required
def notification_mark_read(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id)
    notification.is_read = True
    notification.save()
    notifications = list(Notification.objects.filter(recipient=request.user).order_by('-timestamp'))
    context = {'notifications': notifications}
    return render(request, 'notifications/notification_list.html', context)

# @login_required
# def notification_delete(request, notification_id):
#     notification = get_object_or_404(Notification, pk=notification_id)
#     notification.delete()
#     notifications = list(Notification.objects.filter(recipient=request.user).order_by('-timestamp'))
#     context = {'notifications': notifications}
#     return render(request, 'notifications/notification_list.html', context)

@login_required
def notification_delete(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id)
    notification.delete()
    return redirect('notifications:notification_list')

@login_required
def notification_delete_multiple(request):
    if request.method == 'POST':
        notification_ids = request.POST.getlist('selected_notifications')
        notifications = Notification.objects.filter(pk__in=notification_ids)
        notifications.delete()
    return redirect('notifications:notification_list')
