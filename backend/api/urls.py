from django.urls import path
from .views import (
    BranchListView, ServiceCategoryListView, JoinQueueView,
    CallNextView, StartServiceView, CompleteServiceView,
    QueueStatusView, AnalyticsView, CheckStatusView, SubscribePushView,
    CancelTicketView, NoShowView,
)

urlpatterns = [
    path('branches/', BranchListView.as_view(), name='branches'),
    path('services/', ServiceCategoryListView.as_view(), name='services'),
    path('join/', JoinQueueView.as_view(), name='join-queue'),
    path('check-status/', CheckStatusView.as_view(), name='check-status'),
    path('subscribe-push/', SubscribePushView.as_view(), name='subscribe-push'),
    path('call-next/', CallNextView.as_view(), name='call-next'),
    path('start-service/', StartServiceView.as_view(), name='start-service'),
    path('complete-service/', CompleteServiceView.as_view(), name='complete-service'),
    path('cancel-ticket/', CancelTicketView.as_view(), name='cancel-ticket'),
    path('no-show/', NoShowView.as_view(), name='no-show'),
    path('queue-status/', QueueStatusView.as_view(), name='queue-status'),
    path('analytics/', AnalyticsView.as_view(), name='analytics'),
]