from ..models import Item

def get_items():
    queryset = Item.objects.all()
    return queryset

def create_item(form):
    # Si form es un ModelForm, form.save() ya persiste la instancia.
    item = form.save()
    # No es necesario llamar otra vez a item.save() salvo que hayas usado commit=False
    return item

