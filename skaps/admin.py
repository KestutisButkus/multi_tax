from django.contrib import admin
from .models import (
    Association, Customer, Meter, TaxType, Period, PeriodTax,
    MeterReading, Invoice, InvoiceItem
)

@admin.register(Association)
class AssociationAdmin(admin.ModelAdmin):
    list_display = ("name", "manager")
    search_fields = ("name",)
    list_filter = ("manager",)

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "association", "email", "phone", "balance")
    search_fields = ("full_name", "email")
    list_filter = ("association",)

@admin.register(Meter)
class MeterAdmin(admin.ModelAdmin):
    list_display = ("customer", "meter_type", "unit", "description", "ser_num")
    list_filter = ("meter_type", "unit")
    search_fields = ("customer__full_name", "ser_num")

@admin.register(TaxType)
class TaxTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "association", "distribution_type", "meter_type", "currency")
    list_filter = ("association", "distribution_type", "meter_type", "currency")
    search_fields = ("name",)

@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ("year", "month")
    ordering = ("-year", "-month")

@admin.register(PeriodTax)
class PeriodTaxAdmin(admin.ModelAdmin):
    list_display = ("tax_type", "association", "period", "amount")
    list_filter = ("association", "period", "tax_type")
    search_fields = ("tax_type__name",)

@admin.register(MeterReading)
class MeterReadingAdmin(admin.ModelAdmin):
    list_display = ("meter", "period", "value")
    list_filter = ("meter__meter_type", "period")
    search_fields = ("meter__customer__full_name",)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("number", "customer", "period", "total_amount", "payable_amount", "balance")
    list_filter = ("period",)
    search_fields = ("number", "customer__full_name")

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ("description", "invoice", "quantity", "unit_price", "total", "unit", "currency")
    list_filter = ("invoice__period",)
    search_fields = ("description", "invoice__number")
