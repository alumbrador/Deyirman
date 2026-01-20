from django.contrib import admin
from django.db.models import Sum

from .models import (
    Product, Customer,
    Production, ProductionItem,
    Sale, SaleItem,
    Payment, StockMove
)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "bag_kg", "active", "stock_bags")
    search_fields = ("name",)
    list_filter = ("active",)

    def stock_bags(self, obj):
        ins = StockMove.objects.filter(product=obj, move_type=StockMove.TYPE_IN).aggregate(s=Sum("qty_bag"))["s"] or 0
        outs = StockMove.objects.filter(product=obj, move_type=StockMove.TYPE_OUT).aggregate(s=Sum("qty_bag"))["s"] or 0
        return ins - outs
    stock_bags.short_description = "Qalıq (kisə)"


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "voen")
    search_fields = ("name", "phone", "voen")


class ProductionItemInline(admin.TabularInline):
    model = ProductionItem
    extra = 1


@admin.register(Production)
class ProductionAdmin(admin.ModelAdmin):
    list_display = ("date", "shift", "status", "total_kg_control")
    list_filter = ("shift", "status", "date")
    inlines = [ProductionItemInline]


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("sale_no", "date", "customer", "status", "payment_type", "total_amount", "paid_amount", "debt_amount")
    list_filter = ("status", "payment_type", "date")
    search_fields = ("sale_no", "customer__name")
    inlines = [SaleItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("date", "sale", "amount")
    search_fields = ("sale__sale_no",)


@admin.register(StockMove)
class StockMoveAdmin(admin.ModelAdmin):
    list_display = ("date", "move_type", "source", "product", "qty_bag", "ref_text", "shift")
    list_filter = ("move_type", "source", "date", "shift")
    search_fields = ("ref_text", "product__name")
