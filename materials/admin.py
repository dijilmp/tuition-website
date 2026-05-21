from django.contrib import admin

from .models import ClassLevel, Subject, PDFMaterial


admin.site.register(ClassLevel)
admin.site.register(Subject)
admin.site.register(PDFMaterial)