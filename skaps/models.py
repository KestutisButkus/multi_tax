import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User


METER_TYPES = [
        ("electricity", "Electricity"),
        ("water", "Water"),
        ("gas", "Gas"),
    ]

UNITS = [
    ("kWh", "kWh"),
    ("m3", "m³"),
    ("m2", "m²"),
]

METER_TYPE_UNITS = {
    "electricity": "kWh",
    "water": "m3",
    "gas": "m3",
}


class BaseModel(models.Model):
    """Abstract base model with UUID and timestamps."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Association(BaseModel):
    """Represents a housing association (bendrija)."""
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name


class Period(BaseModel):
    """Represents a year-month accounting period."""
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ("year", "month")
        ordering = ["-year", "-month"]

    def __str__(self):
        return f"{self.year}-{self.month:02d}"


class Customer(BaseModel):
    """Represents a member of the association."""
    association = models.ForeignKey(Association, on_delete=models.CASCADE, related_name="customers")
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                  help_text="Positive = prepaid, Negative = debt")
    floor_area = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.full_name} ({self.association.name})"


class Meter(BaseModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="meters")
    meter_type = models.CharField(max_length=20, choices=METER_TYPES)
    unit = models.CharField(max_length=10, editable=False)  # Priskiriama automatiškai
    description = models.CharField(max_length=100, blank=True)
    ser_num = models.CharField("Serial number", max_length=20, blank=True)

    def clean(self):
        # automatinis unit priskyrimas
        expected_unit = METER_TYPE_UNITS.get(self.meter_type)
        if expected_unit is None:
            raise ValidationError(f"No default unit defined for meter_type '{self.meter_type}'.")
        self.unit = expected_unit

    def save(self, *args, **kwargs):
        self.full_clean()  # iškviečia clean() ir validacijas
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer.full_name} - {self.get_meter_type_display()} ({self.unit})"

    @property
    def unit_display(self):
        return dict(UNITS).get(self.unit, self.unit)


class TaxType(BaseModel):
    """Defines a type of tax/fee with distribution logic."""

    DISTRIBUTION_CHOICES = [
        ("proportional", "Proportional by meter data"),
        ("fixed", "Fixed fee per customer"),
        ("by_area", "Proportional by floor area"),
        ("equal_split", "Split equally among all"),
    ]

    association = models.ForeignKey(Association, on_delete=models.CASCADE, related_name="tax_types")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    distribution_type = models.CharField(max_length=50, choices=DISTRIBUTION_CHOICES)

    meter_type = models.CharField(
        max_length=20,
        choices=METER_TYPES,
        blank=True,
        null=True,
        help_text="Used only if distribution_type='proportional'"
    )

    currency = models.CharField(
        max_length=10,
        choices=[("eur", "€"), ("usd", "$"), ("gbp", "£")],
        default="eur"
    )

    def clean(self):
        # 1. Proporcinis mokestis privalo turėti meter_type
        if self.distribution_type == "proportional" and not self.meter_type:
            raise ValidationError({
                "meter_type": "This field is required when distribution_type is 'proportional'."
            })

        # 2. Kitais atvejais meter_type turi būti tuščias
        if self.distribution_type != "proportional" and self.meter_type:
            raise ValidationError({
                "meter_type": "This field must be empty unless distribution_type is 'proportional'."
            })

    def __str__(self):
        return f"{self.name} ({self.association.name})"



class PeriodTax(BaseModel):
    """Stores tax amounts for a specific association and period."""
    association = models.ForeignKey(Association, on_delete=models.CASCADE, related_name="period_taxes")
    tax_type = models.ForeignKey(TaxType, on_delete=models.CASCADE, related_name="period_taxes")
    period = models.ForeignKey(Period, on_delete=models.CASCADE, related_name="taxes")
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.tax_type.name} {self.amount} {self.tax_type.currency} ({self.period})"





class MeterReading(BaseModel):
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, related_name="readings")
    period = models.ForeignKey(Period, on_delete=models.CASCADE, related_name="meter_readings")
    value = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ("meter", "period")

    def __str__(self):
        return f"{self.meter} ({self.period}): {self.value} {self.meter.unit}"

class Invoice(BaseModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="invoices")
    period = models.ForeignKey(Period, on_delete=models.PROTECT, related_name="invoices")
    number = models.CharField(max_length=50, unique=True)
    date = models.DateField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payable_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.number} - {self.customer.full_name}"


class InvoiceItem(BaseModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # papildomi ryšiai
    meter = models.ForeignKey(Meter, on_delete=models.SET_NULL, null=True, blank=True, related_name="invoice_items")
    period_tax = models.ForeignKey(PeriodTax, on_delete=models.SET_NULL, null=True, blank=True, related_name="invoice_items")

    start_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    end_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    consumed = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    supplier_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_diff = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.description} ({self.total} €)"

    @property
    def unit(self):
        if self.meter:
            return self.meter.get_unit_display()
        if self.period_tax and self.period_tax.tax_type.distribution_type == "by_area":
            return "m²"
        return None

    @property
    def currency(self):
        """Grąžina valiutą iš susieto PeriodTax → TaxType, jei yra."""
        return self.period_tax.tax_type.currency if self.period_tax else None
