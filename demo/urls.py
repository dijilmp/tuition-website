from django.urls import path

from . import views

urlpatterns = [
    path('demo/', views.view_demo, name='view_demo'),
    path('demo/content/', views.demo_content, name='demo_content'),
    path('demo/online-test/<int:test_id>/', views.take_demo_online_test, name='take_demo_online_test'),
    path('demo/online-test/<int:test_id>/submit/', views.submit_demo_online_test, name='submit_demo_online_test'),
    path('demo/online-result/<int:attempt_id>/', views.demo_online_result, name='demo_online_result'),
]
