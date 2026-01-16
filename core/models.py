from django.db import models
from django.contrib.auth.models import User

# Create your models here.



from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Financial(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="financials")

    crm = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    offering = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    minister_tithe = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    general_tithe = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    thanksgiving = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    breakthrough = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    others = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    sunday_school = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    children = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)

    created_at = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "Financial"

    @property
    def total(self):
        return (
            (self.crm or Decimal('0')) +
            (self.offering or Decimal('0')) +
            (self.minister_tithe or Decimal('0')) +
            (self.general_tithe or Decimal('0')) +
            (self.thanksgiving or Decimal('0'))
        )

    @property
    def general_tithe_pct(self):
        return (self.general_tithe or Decimal('0')) * Decimal('0.64')

    @property
    def minister_tithe_pct(self):
        return (self.minister_tithe or Decimal('0')) * Decimal('0.64')

    @property
    def sunday_school_pct(self):
        return (self.sunday_school or Decimal('0')) * Decimal('0.50')

    @property
    def thanksgiving_pct(self):
        return (self.thanksgiving or Decimal('0')) * Decimal('0.70')

    @property
    def crm_pct(self):
        return (self.crm or Decimal('0')) * Decimal('0.50')

    @property
    def children_pct(self):
        return (self.children or Decimal('0')) * Decimal('0.35')

    @property
    def weighted_total(self):
        return (
            self.general_tithe_pct +
            self.minister_tithe_pct +
            self.sunday_school_pct +
            self.thanksgiving_pct +
            self.crm_pct +
            self.children_pct
        )

    def __str__(self):
        return f"Financial record for {self.user}"
