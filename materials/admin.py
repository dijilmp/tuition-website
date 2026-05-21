from django.contrib import admin

from .models import (
    ClassLevel,
    Subject,
    PDFMaterial,
    VideoMaterial,
    PDFAccessLog
)


admin.site.register(ClassLevel)
admin.site.register(Subject)
admin.site.register(PDFMaterial)
admin.site.register(VideoMaterial)


@admin.register(PDFAccessLog)
class PDFAccessLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'pdf', 'accessed_at', 'ip_address')
    list_filter = ('accessed_at', 'user', 'pdf')
    search_fields = ('user__username', 'pdf__title', 'ip_address')