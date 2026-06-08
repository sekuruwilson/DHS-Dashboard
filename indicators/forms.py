from django import forms
from .models import Category, Indicator, IndicatorValue, District, Province

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Chapter 1: Population'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class IndicatorForm(forms.ModelForm):
    class Meta:
        model = Indicator
        fields = ['category', 'name', 'unit', 'year']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2022'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        category = cleaned_data.get('category')
        year = cleaned_data.get('year')

        if name and category and year is not None:
            # Query for duplicate record (case-insensitive name match)
            exists = Indicator.objects.filter(
                name__iexact=name,
                category=category,
                year=year
            )
            
            # Exclude current record if editing
            if self.instance and self.instance.pk:
                exists = exists.exclude(pk=self.instance.pk)
                
            if exists.exists():
                raise forms.ValidationError(
                    f"An indicator with the name '{name}' already exists for category '{category}' in the year {year}."
                )
        return cleaned_data

class DataValueForm(forms.ModelForm):
    indicator = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = IndicatorValue
        fields = ['indicator', 'district', 'data_label', 'year', 'value']
        widgets = {
            'district': forms.Select(attrs={'class': 'form-select'}),
            'data_label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Total'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2022'}),
            'value': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        names = sorted(list(set(Indicator.objects.values_list('name', flat=True))))
        self.fields['indicator'].choices = [(name, name) for name in names]
        if self.instance and self.instance.pk:
            self.fields['indicator'].initial = self.instance.indicator.name

    def clean_indicator(self):
        indicator_name = self.cleaned_data.get('indicator')
        year_val = self.data.get('year')
        try:
            year = int(year_val)
        except (ValueError, TypeError):
            year = 2022
            
        template_ind = Indicator.objects.filter(name=indicator_name).first()
        if not template_ind:
            raise forms.ValidationError("Select a valid indicator.")
            
        indicator, _ = Indicator.objects.get_or_create(
            name=indicator_name,
            year=year,
            defaults={
                'category': template_ind.category,
                'unit': template_ind.unit
            }
        )
        return indicator

class ProvinceForm(forms.ModelForm):
    class Meta:
        model = Province
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class DistrictForm(forms.ModelForm):
    class Meta:
        model = District
        fields = ['province', 'name']
        widgets = {
            'province': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class SingleIndicatorDataForm(forms.ModelForm):
    indicator = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = IndicatorValue
        fields = ['indicator', 'district', 'data_label', 'year', 'value']
        widgets = {
            'district': forms.Select(attrs={'class': 'form-select'}),
            'data_label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Total'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2022'}),
            'value': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        names = sorted(list(set(Indicator.objects.values_list('name', flat=True))))
        self.fields['indicator'].choices = [(name, name) for name in names]
        if self.instance and self.instance.pk:
            self.fields['indicator'].initial = self.instance.indicator.name

    def clean_indicator(self):
        indicator_name = self.cleaned_data.get('indicator')
        year_val = self.data.get('year')
        try:
            year = int(year_val)
        except (ValueError, TypeError):
            year = 2022
            
        template_ind = Indicator.objects.filter(name=indicator_name).first()
        if not template_ind:
            raise forms.ValidationError("Select a valid indicator.")
            
        indicator, _ = Indicator.objects.get_or_create(
            name=indicator_name,
            year=year,
            defaults={
                'category': template_ind.category,
                'unit': template_ind.unit
            }
        )
        return indicator

class IndicatorJSONUploadForm(forms.Form):
    category = forms.ModelChoiceField(queryset=Category.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}))
    year = forms.IntegerField(initial=2022, widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 2000, 'max': 2100}))
    json_file = forms.FileField(widget=forms.FileInput(attrs={'class': 'form-control'}))


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={'class': 'form-control'}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class DHSComputationForm(forms.Form):
    year = forms.IntegerField(
        initial=2022,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 2000, 'max': 2100}),
        help_text="The year of the survey dataset (e.g., 2022 or 2025)."
    )
    dta_files = MultipleFileField(
        help_text="Upload one or multiple raw .DTA files (e.g. RWPR81FL.DTA, RWIR81FL.DTA, etc.)."
    )

