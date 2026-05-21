from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from django.contrib.auth import views as auth_views

from materials.views import (
    dashboard,
    subject_materials,
    view_pdf,
    protected_pdf_file
)

urlpatterns = [

    path('admin/', admin.site.urls),

    path(
        '',
        auth_views.LoginView.as_view(
            template_name='login.html'
        ),
        name='login'
    ),

    path(
        'logout/',
        auth_views.LogoutView.as_view(),
        name='logout'
    ),

    path(
        'dashboard/',
        dashboard,
        name='dashboard'
    ),

    path(
        'subject/<int:subject_id>/',
        subject_materials,
        name='subject_materials'
    ),

    path(
        'pdf/<int:pdf_id>/',
        view_pdf,
        name='view_pdf'
    ),

    path(
        'pdf-file/<int:pdf_id>/',
        protected_pdf_file,
        name='protected_pdf_file'
    ),

]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )