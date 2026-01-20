from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Production, Sale, StockMove


def get_stock_bags(product):
    ins = StockMove.objects.filter(product=product, move_type=StockMove.TYPE_IN).aggregate(s=Sum("qty_bag"))["s"] or 0
    outs = StockMove.objects.filter(product=product, move_type=StockMove.TYPE_OUT).aggregate(s=Sum("qty_bag"))["s"] or 0
    return ins - outs


def next_sale_no():
    year = timezone.now().year
    prefix = f"S-{year}-"
    last = Sale.objects.filter(sale_no__startswith=prefix).order_by("-sale_no").first()
    if not last:
        return f"{prefix}000001"
    last_num = int(last.sale_no.split("-")[-1])
    return f"{prefix}{last_num + 1:06d}"


@receiver(pre_save, sender=Sale)
def sale_autonumber(sender, instance: Sale, **kwargs):
    if not instance.sale_no:
        instance.sale_no = next_sale_no()


@receiver(post_save, sender=Production)
def production_confirm_creates_stock(sender, instance: Production, created, **kwargs):
    if instance.status != Production.STATUS_CONFIRMED:
        return

    ref = f"PROD-{instance.id}"
    if StockMove.objects.filter(source=StockMove.SRC_PRODUCTION, ref_text=ref).exists():
        return

    with transaction.atomic():
        for it in instance.items.all():
            StockMove.objects.create(
                date=instance.date,
                move_type=StockMove.TYPE_IN,
                source=StockMove.SRC_PRODUCTION,
                product=it.product,
                qty_bag=it.qty_bag,
                ref_text=ref,
                shift=instance.shift,
                note="İstehsaldan giriş",
            )


@receiver(post_save, sender=Sale)
def sale_confirm_creates_stock(sender, instance: Sale, created, **kwargs):
    if instance.status != Sale.STATUS_CONFIRMED:
        return

    ref = instance.sale_no
    if StockMove.objects.filter(source=StockMove.SRC_SALE, ref_text=ref).exists():
        return

    with transaction.atomic():
        # stok yoxla
        for it in instance.items.all():
            available = get_stock_bags(it.product)
            if it.qty_bag > available:
                raise ValidationError(
                    f"Anbar qalığı yetərsizdir: {it.product.name}. Qalıq: {available} kisə, tələb: {it.qty_bag} kisə"
                )

        # OUT yaz
        for it in instance.items.all():
            StockMove.objects.create(
                date=instance.date,
                move_type=StockMove.TYPE_OUT,
                source=StockMove.SRC_SALE,
                product=it.product,
                qty_bag=it.qty_bag,
                ref_text=ref,
                note="Satışdan çıxış",
            )

        # məbləğ hesabla
        total = sum([it.line_total for it in instance.items.all()])
        Sale.objects.filter(pk=instance.pk).update(
    total_amount=total,
    debt_amount=(total or 0) - (instance.paid_amount or 0),
)

