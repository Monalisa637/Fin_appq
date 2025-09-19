from django.db import models

class FinancialDocument(models.Model):
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class FinancialData(models.Model):
    document = models.ForeignKey(FinancialDocument, on_delete=models.CASCADE)
    key = models.CharField(max_length=200)
    value = models.CharField(max_length=200)
