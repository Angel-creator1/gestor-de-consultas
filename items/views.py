from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import ItemForm
from .logic.item_logic import get_items, create_item

def item_list(request):
    items = get_items()
    context = {
        'item_list': items
    }
    return render(request, 'Item/items.html', context)

def item_create(request):
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            create_item(form)
            messages.add_message(request, messages.SUCCESS, 'Successfully created item')
            return HttpResponseRedirect(reverse('itemCreate'))
        else:
            print(form.errors)
    else:
        form = ItemForm()

    context = {
        'form': form,
    }
    return render(request, 'Item/itemCreate.html', context)
