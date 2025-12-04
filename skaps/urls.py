from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),

    # Associations
    path("associations/add/", views.add_association, name="add_association"),
    path("associations/", views.associations_list, name="associations_list"),
    path("association/<uuid:association_id>/", views.association_dashboard, name="association_dashboard"),

    # Customers
    path("association/<uuid:association_id>/customers/", views.customers_list, name="customers_list"),
    path("association/<uuid:association_id>/customers/add/", views.add_customer, name="add_customer"),
    path("association/<uuid:association_id>/customers/<uuid:customer_id>/", views.customer_dashboard,
         name="customer_dashboard"),
    path("association/<uuid:association_id>/customers/<uuid:customer_id>/edit/", views.edit_customer,
         name="edit_customer"),

    # Taxes
    path("association/<uuid:association_id>/taxes/", views.association_taxes, name="association_taxes"),
    path("association/<uuid:association_id>/taxes/add/", views.add_tax, name="add_tax"),
    path("association/<uuid:association_id>/taxes/<uuid:tax_id>/edit/", views.tax_edit, name="tax_edit"),

    # Period taxes
    path("association/<uuid:association_id>/period-taxes/", views.period_taxes, name="period_taxes"),
    path("association/<uuid:association_id>/period-taxes/add/", views.add_period_tax, name="add_period_tax"),

    # Periods (global)
    path("periods/", views.period_list, name="period_list"),
    path("periods/add/", views.add_period, name="add_period"),

    # Meters
    path("association/<uuid:association_id>/meters/", views.meter_list, name="meter_list"),
    path("customers/<uuid:customer_id>/meters/add/", views.add_meter, name="add_meter"),
    path("customers/<uuid:customer_id>/meters/<uuid:meter_id>/edit/", views.edit_meter, name="edit_meter"),

    # Meter readings
    path("customers/<uuid:customer_id>/meter-readings/add/", views.add_meter_reading, name="add_meter_reading"),
    path("customers/<uuid:customer_id>/meter-readings/", views.meter_readings, name="meter_readings"),

    # Invoices
    path(
        "customers/<uuid:customer_id>/invoices/<uuid:invoice_id>/",
        views.invoice_detail,
        name="invoice_detail"
    ),

    # Generate invoice
    path(
        "customers/<uuid:customer_id>/invoices/generate/<uuid:period_id>/",
        views.generate_invoice_view,
        name="generate_invoice"
    ),

]
