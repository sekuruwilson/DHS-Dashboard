from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        # Remove "Chapter X:" prefix if present, return only the descriptive name
        if ':' in self.name:
            return self.name.split(':', 1)[1].strip()
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

class Province(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class District(models.Model):
    name = models.CharField(max_length=100)
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name='districts')
    
    def __str__(self):
        return f"{self.name} ({self.province.name})"

class Indicator(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='indicators')
    unit = models.CharField(max_length=50)
    year = models.IntegerField(default=2022)

    def __str__(self):
        return f"{self.name} ({self.year})"

from django.contrib.auth.models import User

class ReportDraft(models.Model):
    title      = models.CharField(max_length=255, default='Untitled Draft')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='report_drafts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    content    = models.JSONField(default=dict)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-updated_at']


class IndicatorValue(models.Model):
    indicator = models.ForeignKey(Indicator, on_delete=models.CASCADE, related_name='values')
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='indicator_values')
    data_label = models.CharField(max_length=100, default='Total') # e.g. "Total", "Observed, Fixed place"
    year = models.IntegerField(default=2022)
    value = models.FloatField()

    def __str__(self):
        return f"{self.indicator.name} - {self.district.name} ({self.data_label}) - {self.year}"
