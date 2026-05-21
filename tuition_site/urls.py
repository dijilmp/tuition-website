from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView, LogoutView

from materials.views import dashboard, subject_materials

urlpatterns = [

    path('admin/', admin.site.urls),

    path('', LoginView.as_view(template_name='login.html'), name='login'),

    path('login/', LoginView.as_view(template_name='login.html'), name='login'),

    path('logout/', LogoutView.as_view(), name='logout'),

    path('dashboard/', dashboard, name='dashboard'),

    path('subject/<int:subject_id>/',
         subject_materials,
         name='subject_materials'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)