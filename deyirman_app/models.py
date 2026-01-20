from django.db import models
from django.utils import timezone

class Product(models.Model):
    name = models.CharField("Məhsul adı", max_length=100, unique=True)
    bag_kg = models.PositiveIntegerField("1 kisə (kg)")
    active = models.BooleanField("Aktiv", default=True)

    def __str__(self):
        return self.name


class Customer(models.Model):
    name = models.CharField("Müştəri adı", max_length=150)
    phone = models.CharField("Telefon", max_length=50, blank=True)
    voen = models.CharField("VÖEN", max_length=50, blank=True)
    note = models.TextField("Qeyd", blank=True)

    def __str__(self):
        return self.name


class Production(models.Model):
    SHIFT_DAY = "DAY"
    SHIFT_NIGHT = "NIGHT"
    SHIFT_CHOICES = [(SHIFT_DAY, "Gündüz"), (SHIFT_NIGHT, "Gecə")]

    STATUS_DRAFT = "DRAFT"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_CHOICES = [(STATUS_DRAFT, "Qaralama"), (STATUS_CONFIRMED, "Təsdiqlənmiş")]

    date = models.DateField("Tarix", default=timezone.now)
    shift = models.CharField("Növbə", max_length=10, choices=SHIFT_CHOICES)
    status = models.CharField("Status", max_length=10, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    total_kg_control = models.PositiveIntegerField("Ümumi istehsal (kg) - kontrol", default=0)
    note = models.TextField("Qeyd", blank=True)

    def __str__(self):
        return f"{self.date} - {self.get_shift_display()}"


class ProductionItem(models.Model):
    production = models.ForeignKey(Production, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    qty_bag = models.PositiveIntegerField("Kisə sayı")

    @property
    def qty_kg(self):
        return self.qty_bag * self.product.bag_kg


class Sale(models.Model):
    PAY_CASH = "CASH"
    PAY_CREDIT = "CREDIT"
    PAY_PARTIAL = "PARTIAL"
    PAY_CHOICES = [(PAY_CASH, "Nəğd"), (PAY_CREDIT, "Nisyə"), (PAY_PARTIAL, "Qismən")]

    STATUS_DRAFT = "DRAFT"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Qaralama"),
        (STATUS_CONFIRMED, "Təsdiqlənmiş"),
        (STATUS_CANCELLED, "Ləğv"),
    ]

    sale_no = models.CharField("Satış No", max_length=20, unique=True, blank=True)

    date = models.DateField("Tarix", default=timezone.now)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    status = models.CharField("Status", max_length=10, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    payment_type = models.CharField("Ödəniş növü", max_length=10, choices=PAY_CHOICES, default=PAY_CREDIT)

    total_amount = models.DecimalField("Cəm", max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField("Ödənən", max_digits=12, decimal_places=2, default=0)
    debt_amount = models.DecimalField("Borc", max_digits=12, decimal_places=2, default=0)

    note = models.TextField("Qeyd", blank=True)

    def __str__(self):
        return self.sale_no


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    qty_bag = models.PositiveIntegerField("Kisə sayı")
    unit_price_bag = models.DecimalField("Qiymət (AZN/kisə)", max_digits=12, decimal_places=2)

    @property
    def line_total(self):
        return self.qty_bag * self.unit_price_bag

    @property
    def qty_kg(self):
        return self.qty_bag * self.product.bag_kg


class Payment(models.Model):
    date = models.DateField("Tarix", default=timezone.now)
    sale = models.ForeignKey(Sale, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField("Məbləğ (AZN)", max_digits=12, decimal_places=2)
    note = models.TextField("Qeyd", blank=True)

    def __str__(self):
        return f"{self.sale.sale_no} - {self.amount} AZN"


class StockMove(models.Model):
    TYPE_IN = "IN"
    TYPE_OUT = "OUT"
    TYPE_CHOICES = [(TYPE_IN, "Giriş"), (TYPE_OUT, "Çıxış")]

    SRC_PRODUCTION = "PRODUCTION"
    SRC_SALE = "SALE"
    SRC_CHOICES = [(SRC_PRODUCTION, "İstehsal"), (SRC_SALE, "Satış")]

    date = models.DateField("Tarix", default=timezone.now)
    move_type = models.CharField("Tip", max_length=5, choices=TYPE_CHOICES)
    source = models.CharField("Mənbə", max_length=20, choices=SRC_CHOICES)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    qty_bag = models.PositiveIntegerField("Kisə sayı")

    ref_text = models.CharField("İstinad", max_length=50, blank=True)  # sale_no və ya production id
    shift = models.CharField("Növbə (istehsal üçün)", max_length=10, blank=True)  # DAY/NIGHT
    note = models.TextField("Qeyd", blank=True)

    @property
    def qty_kg(self):
        return self.qty_bag * self.product.bag_kg
