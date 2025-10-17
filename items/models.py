from django.db import models

class Item(models.Model):
    STATE_VERIFIED = 'Verificado'
    STATE_IN_PROGRESS = 'Alistamiento'

    STATE_CHOICES = [
        (STATE_VERIFIED, 'Verificado'),
        (STATE_IN_PROGRESS, 'Alistamiento'),
    ]

    name = models.CharField(max_length=50)
    state = models.CharField(max_length=50, choices=STATE_CHOICES, default=STATE_IN_PROGRESS)
    

    def __str__(self):
        return '{}'.format(self.name)
