from django.db import models


class ClassLevel(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Subject(models.Model):
    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.class_level} - {self.name}"


class PDFMaterial(models.Model):
    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    title = models.CharField(max_length=200)

    pdf_file = models.FileField(upload_to='pdfs/')

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title