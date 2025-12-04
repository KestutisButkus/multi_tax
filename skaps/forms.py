from django import forms
from django.forms import inlineformset_factory

from .models import TaxType, PeriodTax, Period, Meter, MeterReading, Customer, Association


class AssociationForm(forms.ModelForm):
    class Meta:
        model = Association
        fields = ["name", "description", "manager"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "manager": forms.Select(attrs={"class": "form-select"}),
        }

class TaxTypeForm(forms.ModelForm):
    class Meta:
        model = TaxType
        fields = ["name", "description", "distribution_type", "currency", "meter_type"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "distribution_type": forms.Select(attrs={"class": "form-select"}),
            "currency": forms.Select(attrs={"class": "form-select"}),
            "meter_type": forms.Select(attrs={"class": "form-select"}),
        }

class PeriodTaxForm(forms.ModelForm):
    class Meta:
        model = PeriodTax
        fields = ["period", "tax_type", "amount"]
        widgets = {
            "period": forms.Select(attrs={"class": "form-select"}),
            "tax_type": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }


class PeriodForm(forms.ModelForm):
    class Meta:
        model = Period
        fields = ["year", "month"]
        widgets = {
            "year": forms.NumberInput(attrs={"class": "form-control", "min": 2000, "max": 2100}),
            "month": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 12}),
        }




class MeterReadingForm(forms.ModelForm):
    class Meta:
        model = MeterReading
        fields = ["meter", "period", "value"]
        widgets = {
            "meter": forms.Select(attrs={"class": "form-select"}),
            "period": forms.Select(attrs={"class": "form-select"}),
            "value": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["association", "full_name", "email", "phone", "address", "floor_area", "balance"]
        widgets = {
            "association": forms.Select(attrs={"class": "form-select"}),
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "floor_area": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "balance": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

# Inline formset – skaitikliams priskirti klientui
class MeterForm(forms.ModelForm):
    class Meta:
        model = Meter
        fields = ["meter_type", "ser_num", "description"]
        widgets = {
            "meter_type": forms.Select(attrs={"class": "form-select"}),
            "ser_num": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
        }

MeterFormSet = inlineformset_factory(
    Customer, Meter,
    form=MeterForm,
    extra=1,
    can_delete=True
)
