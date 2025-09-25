from ..models import Item

def get_items():
    queryset = Item.objects.all()
    return queryset

def create_item(form):
    item = form.save()
    item.save()
    return ()
