import uuid
from decimal import Decimal

from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import render, get_object_or_404, redirect
from .forms import TaxTypeForm, PeriodTaxForm, PeriodForm, MeterForm, MeterReadingForm, MeterFormSet, CustomerForm, \
    AssociationForm
from .models import TaxType, Period, Meter, MeterReading, Customer, Association, Invoice, InvoiceItem, PeriodTax


def add_association(request):
    if request.method == "POST":
        form = AssociationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("associations_list")
    else:
        form = AssociationForm()
    return render(request, "skaps/add_association.html", {"form": form})


def associations_list(request):
    associations = Association.objects.all()
    return render(request, "skaps/associations_list.html", {"associations": associations})


def association_dashboard(request, association_id):
    association = get_object_or_404(Association, id=association_id)
    return render(request, "skaps/association_dashboard.html", {"association": association})


def index(request):
    association = Association.objects.first()
    context = {"association": association}
    return render(request, "skaps/index.html", context)


def customers_list(request, association_id):
    association = get_object_or_404(Association, id=association_id)
    customers = Customer.objects.filter(association=association)
    return render(request, "skaps/customers_list.html", {"association": association, "customers": customers})


def tax_list(request):
    taxes = TaxType.objects.all()
    return render(request, "skaps/tax_list.html", {"taxes": taxes})


def association_taxes(request, association_id):
    association = get_object_or_404(Association, id=association_id)
    taxes = association.tax_types.all()
    return render(request, "skaps/association_taxes.html", {
        "association": association,
        "taxes": taxes
    })


def add_tax(request, association_id):
    association = get_object_or_404(Association, id=association_id)
    if request.method == "POST":
        form = TaxTypeForm(request.POST)
        if form.is_valid():
            tax = form.save(commit=False)
            tax.association = association
            tax.save()
            return redirect("association_taxes", association_id=association.id)
    else:
        form = TaxTypeForm()
    return render(request, "skaps/add_tax.html", {
        "form": form,
        "association": association
    })

def tax_edit(request, association_id, tax_id):
    tax = get_object_or_404(TaxType, pk=tax_id, association_id=association_id)

    if request.method == "POST":
        form = TaxTypeForm(request.POST, instance=tax)
        if form.is_valid():
            form.save()
            return redirect("association_taxes", association_id=association_id)
    else:
        form = TaxTypeForm(instance=tax)

    return render(request, "skaps/tax_edit.html", {"form": form, "tax": tax})



def apply_distribution(customer, period_tax, period):
    tax_type = period_tax.tax_type
    amount = period_tax.amount

    if tax_type.distribution_type == "fixed":
        # fiksuotas mokestis kiekvienam klientui
        return amount

    elif tax_type.distribution_type == "equal_split":
        # padalinam visiems klientams po lygiai
        total_customers = customer.association.customers.count()
        print("klientų skaičius grupėje", total_customers)
        return amount / total_customers if total_customers else 0

    elif tax_type.distribution_type == "by_area":
        # proporcingai pagal plotą (pvz. floor_area laukas Customer modelyje)
        total_area = customer.association.customers.aggregate(total=Sum("floor_area"))["total"] or 0
        return (customer.floor_area / total_area) * amount if total_area else 0

    elif tax_type.distribution_type == "proportional":
        # proporcingai pagal skaitiklių duomenis (pvz. electricity)
        total_consumption = MeterReading.objects.filter(
            meter__customer__association=customer.association,
            period=period
        ).aggregate(total=Sum("value"))["total"] or 0

        customer_consumption = MeterReading.objects.filter(
            meter__customer=customer,
            period=period
        ).aggregate(total=Sum("value"))["total"] or 0

        return (customer_consumption / total_consumption) * amount if total_consumption else 0

    return 0


def period_taxes(request, association_id):
    association = get_object_or_404(Association, id=association_id)
    taxes = association.period_taxes.select_related("tax_type", "period").all()
    return render(request, "skaps/period_taxes.html", {
        "association": association,
        "taxes": taxes
    })


def add_period_tax(request, association_id):
    association = get_object_or_404(Association, id=association_id)
    if request.method == "POST":
        form = PeriodTaxForm(request.POST)
        if form.is_valid():
            period_tax = form.save(commit=False)
            period_tax.association = association
            period_tax.save()
            return redirect("period_taxes", association_id=association.id)
    else:
        form = PeriodTaxForm()
    return render(request, "skaps/add_period_tax.html", {
        "form": form,
        "association": association
    })


def add_period(request):
    if request.method == "POST":
        form = PeriodForm(request.POST)
        if form.is_valid():
            # užtikrinam unikalumą
            year = form.cleaned_data["year"]
            month = form.cleaned_data["month"]
            period, created = Period.objects.get_or_create(year=year, month=month)
            return redirect("period_list")
    else:
        form = PeriodForm()
    return render(request, "skaps/add_period.html", {"form": form})


def period_list(request):
    periods = Period.objects.all().order_by("-year", "-month")
    return render(request, "skaps/period_list.html", {"periods": periods})


def meter_list(request, association_id):
    association = get_object_or_404(Association, id=association_id)
    meters = Meter.objects.filter(customer__association=association).select_related("customer")
    return render(request, "skaps/meter_list.html", {"association": association, "meters": meters})


def add_meter(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == "POST":
        form = MeterForm(request.POST)
        if form.is_valid():
            meter = form.save(commit=False)
            meter.customer = customer
            meter.save()
            # vietoje meter_list → redirectinam į customer_dashboard
            return redirect("customer_dashboard", association_id=customer.association.id, customer_id=customer.id)
    else:
        form = MeterForm()
    return render(request, "skaps/add_meter.html", {"form": form, "customer": customer})


def meter_readings(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    readings = MeterReading.objects.filter(meter__customer=customer).select_related("meter", "period")
    return render(request, "skaps/meter_readings.html", {"customer": customer, "readings": readings})


def add_meter_reading(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == "POST":
        form = MeterReadingForm(request.POST)
        if form.is_valid():
            reading = form.save(commit=False)
            # užtikrinam, kad rodmuo priklauso tam klientui
            if reading.meter.customer != customer:
                messages.error(request, "Pasirinktas skaitiklis nepriklauso šiam klientui.")
            else:
                reading.save()
                return redirect("meter_readings", customer_id=customer.id)
    else:
        form = MeterReadingForm()
    return render(request, "skaps/add_meter.html", {"form": form, "customer": customer})


def edit_meter(request, customer_id, meter_id):
    customer = get_object_or_404(Customer, id=customer_id)
    meter = get_object_or_404(Meter, id=meter_id, customer=customer)

    if request.method == "POST":
        form = MeterForm(request.POST, instance=meter)
        if form.is_valid():
            form.save()
            return redirect("customer_dashboard", association_id=customer.association.id, customer_id=customer.id)
    else:
        form = MeterForm(instance=meter)

    return render(request, "skaps/edit_meter.html", {"form": form, "customer": customer, "meter": meter})


def add_customer(request, association_id):
    association = get_object_or_404(Association, id=association_id)
    if request.method == "POST":
        form = CustomerForm(request.POST)
        formset = MeterFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            customer = form.save(commit=False)
            customer.association = association  # priskiri bendriją
            customer.save()
            meters = formset.save(commit=False)
            for m in meters:
                m.customer = customer
                m.save()
            return redirect("customers_list", association_id=association.id)
    else:
        form = CustomerForm()
        formset = MeterFormSet()
    return render(request, "skaps/add_customer.html", {"form": form, "formset": formset, "association": association})


def customer_dashboard(request, association_id, customer_id):
    association = get_object_or_404(Association, id=association_id)
    customer = get_object_or_404(Customer, id=customer_id, association=association)
    meters = customer.meters.all()
    periods = Period.objects.filter(taxes__association=association).distinct().order_by("-year", "-month")

    return render(
        request,
        "skaps/customer_dashboard.html",
        {
            "association": association,
            "customer": customer,
            "meters": meters,
            "periods": periods,
        }
    )


def edit_customer(request, association_id, customer_id):
    association = get_object_or_404(Association, id=association_id)
    customer = get_object_or_404(Customer, id=customer_id, association=association)

    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        formset = MeterFormSet(request.POST, instance=customer)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect("customers_list", association_id=association.id)
    else:
        form = CustomerForm(instance=customer)
        formset = MeterFormSet(instance=customer)

    return render(
        request,
        "skaps/edit_customer.html",
        {"form": form, "formset": formset, "association": association, "customer": customer},
    )


def generate_invoice(customer, period):
    print("Generating invoice for:", customer, period)

    items = []
    total_amount = 0

    period_taxes = PeriodTax.objects.filter(
        association=customer.association,
        period=period
    )

    # Kiekvieną distribution_type apdorojame atskiroje funkcijoje
    for pt in period_taxes:
        if pt.tax_type.distribution_type == "proportional":
            line_items, subtotal = invoices_proportional(customer, pt, period)
        elif pt.tax_type.distribution_type == "fixed":
            line_items, subtotal = invoices_fixed(customer, pt, period)
        elif pt.tax_type.distribution_type == "by_area":
            line_items, subtotal = invoices_by_area(customer, pt, period)
        elif pt.tax_type.distribution_type == "equal_split":
            line_items, subtotal = invoices_equal_split(customer, pt, period)
        else:
            continue

        items.extend(line_items)
        total_amount += subtotal

    # Sukuriame Invoice
    if not items:
        return None

    invoice = Invoice.objects.create(
        customer=customer,
        period=period,
        number=f"INV-{period.year}{period.month:02d}-{customer.id.hex[:6]}-{uuid.uuid4().hex[:4]}",
        total_amount=total_amount,
        payable_amount=total_amount,
        balance=0,
    )

    # Sukuriame InvoiceItem
    for item in items:
        InvoiceItem.objects.create(
            invoice=invoice,
            description=item["description"],
            quantity=item["quantity"],
            unit_price=item["unit_price"],
            total=item["total"],
            start_value=item.get("start_value"),
            end_value=item.get("end_value"),
            consumed=item.get("consumed"),
            supplier_amount=item.get("supplier_amount"),
            total_diff=item.get("total_diff"),
            meter=item.get("meter"),
            period_tax=item.get("period_tax"),
        )

    return invoice

def invoices_fixed(customer, pt, period):
    line_total = apply_distribution(customer, pt, period)
    item = {
        "description": f"{pt.tax_type.name} ({pt.tax_type.get_distribution_type_display()})",
        "quantity": 1,
        "unit_price": line_total,
        "total": line_total,
        "currency": pt.tax_type.currency,
        "period_tax": pt,
    }
    return [item], line_total

def invoices_equal_split(customer, pt, period):
    line_total = apply_distribution(customer, pt, period)
    item = {
        "description": f"{pt.tax_type.name} ({pt.tax_type.get_distribution_type_display()})",
        "quantity": 1,
        "unit_price": line_total,
        "total": line_total,
        "currency": pt.tax_type.currency,
        "period_tax": pt,
    }
    return [item], line_total

def invoices_by_area(customer, pt, period):
    total_floor_area = Customer.objects.filter(
        association=customer.association
    ).aggregate(total=Sum("floor_area"))["total"] or 0

    if total_floor_area > 0:
        unit_price = pt.amount / Decimal(total_floor_area)
        line_total = customer.floor_area * unit_price
    else:
        unit_price = Decimal("0")
        line_total = Decimal("0")

    item = {
        "description": f"{pt.tax_type.name} ({pt.tax_type.get_distribution_type_display()})",
        "quantity": customer.floor_area,
        "unit_price": unit_price,
        "total": line_total,
        "currency": pt.tax_type.currency,
        "period_tax": pt,
    }
    print(item)
    return [item], line_total

def invoices_proportional(customer, pt, period):
    items = []
    subtotal = 0

    meter_type = pt.tax_type.meter_type
    if not meter_type:
        return [], 0

    for meter in customer.meters.filter(meter_type=meter_type):
        current = meter.readings.filter(period=period).first()
        previous = meter.readings.filter(
            period__year=period.year,
            period__month=period.month - 1
        ).first()

        if not current:
            continue  # be dabartinio rodmens nieko nerodome

        if previous:
            consumed = current.value - previous.value
            start_value = previous.value
        else:
            consumed = 0
            start_value = None

        end_value = current.value

        # Bendras suvartojimas visai asociacijai to tipo
        total_consumption = MeterReading.objects.filter(
            meter__customer__association=pt.association,
            meter__meter_type=meter_type,
            period=period
        ).aggregate(total=Sum("value"))["total"] or 0

        prev_total = MeterReading.objects.filter(
            meter__customer__association=pt.association,
            meter__meter_type=meter_type,
            period__year=period.year,
            period__month=period.month - 1
        ).aggregate(total=Sum("value"))["total"] or 0

        total_diff = total_consumption - prev_total if prev_total else total_consumption
        unit_price = pt.amount / Decimal(total_diff) if total_diff > 0 else Decimal("0")

        line_total = round(consumed * unit_price, 2)
        subtotal += line_total

        items.append({
            "description": f"{pt.tax_type.name} ({pt.tax_type.get_distribution_type_display()})",
            "quantity": consumed,
            "start_value": start_value,
            "end_value": end_value,
            "consumed": consumed,
            "unit_price": unit_price,
            "total": line_total,
            "unit": meter.unit_display,
            "currency": pt.tax_type.currency,
            "meter": meter,
            "period_tax": pt,
        })

    return items, subtotal


def generate_invoice_view(request, customer_id, period_id):
    customer = get_object_or_404(Customer, id=customer_id)
    period = get_object_or_404(Period, id=period_id)

    invoice = generate_invoice(customer, period)
    if not invoice:
        messages.error(request, "Nepavyko sugeneruoti sąskaitos – nėra duomenų arba mokesčių.")
        return redirect("customer_dashboard", association_id=customer.association.id, customer_id=customer.id)

    # redirect be period_id
    return redirect("invoice_detail", customer_id=customer.id, invoice_id=invoice.id)


def invoice_detail(request, customer_id, invoice_id):
    customer = get_object_or_404(Customer, id=customer_id)
    invoice = get_object_or_404(Invoice, id=invoice_id, customer=customer)

    # Surikiuojame: pirma ne-skaitikliai (consumed=False arba None), tada skaitikliai
    items = invoice.items.all().order_by('consumed')

    # Sukuriame sąrašą su footnote numeriais
    items_with_footnotes = []
    footnote_num = 1

    for item in items:
        footnote_number = None
        if item.period_tax and item.period_tax.tax_type.description:
            footnote_number = footnote_num
            footnote_num += 1

        items_with_footnotes.append({
            'item': item,
            'footnote_number': footnote_number
        })

    return render(
        request,
        "skaps/invoice_detail.html",
        {
            "customer": customer,
            "invoice": invoice,
            "items": items,
            "items_with_footnotes": items_with_footnotes
        },
    )