from django.db import models


class FPDSFABSUpdate(models.Model):
    last_update = models.DateField(blank=False, null=False)

    class Meta:
        managed = True
        db_table = 'fpds_fabs_update'
