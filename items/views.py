from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import ItemForm
from .logic.item_logic import get_items, create_item
import json
import os
import pika
from django.conf import settings
from django.shortcuts import render, reverse, HttpResponseRedirect
from django.contrib import messages
from .forms import ItemForm
from .logic import create_item 

def item_list(request):
    items = get_items()
    context = {
        'item_list': items
    }
    return render(request, 'items/items.html', context)



def item_create(request):
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            # --- CREAR EL ITEM (tu función)
            try:
                item = create_item(form)  # si retorna el objeto creado, lo usamos
            except Exception as e:
                # Si hay error al crear, mostramos y no publicamos
                messages.add_message(request, messages.ERROR, f'Error creando item: {e}')
                return render(request, 'items/itemCreate.html', {'form': form})

            # --- PREPARAR PAYLOAD
            # Intentamos sacar id u otros campos del objeto retornado.
            payload_data = {}
            if item is not None:
                # intenta extraer atributos típicos; si fallan, caemos a cleaned_data
                try:
                    payload_data['id'] = getattr(item, 'id', None)
                    # Ajusta estos nombres según tu modelo
                    payload_data['name'] = getattr(item, 'name', None)
                    payload_data['created_by'] = getattr(item, 'created_by', None)
                except Exception:
                    payload_data = form.cleaned_data
            else:
                payload_data = form.cleaned_data

            payload = {
                'action': 'created',
                'model': 'Item',
                'data': payload_data
            }

            # --- PUBLICAR EN RABBITMQ
            # Lee configuración desde settings o variables de entorno
            rabbit_host = getattr(settings, "RABBIT_HOST", os.environ.get("RABBIT_HOST", "127.0.0.1"))
            rabbit_user = getattr(settings, "RABBIT_USER", os.environ.get("RABBIT_USER", "monitoring_user"))
            rabbit_password = getattr(settings, "RABBIT_PASSWORD", os.environ.get("RABBIT_PASSWORD", "isis2503"))
            exchange = getattr(settings, "RABBIT_EXCHANGE", os.environ.get("RABBIT_EXCHANGE", "monitoring_measurements"))
            # routing key: cámbiala si quieres algo semántico
            routing_key = getattr(settings, "RABBIT_ROUTING_KEY", os.environ.get("RABBIT_ROUTING_KEY", "ML.505.Item"))

            try:
                credentials = pika.PlainCredentials(rabbit_user, rabbit_password)
                params = pika.ConnectionParameters(host=rabbit_host, credentials=credentials)
                connection = pika.BlockingConnection(params)
                channel = connection.channel()
                channel.exchange_declare(exchange=exchange, exchange_type='topic', durable=False)

                # Serializamos a JSON estándar (dobles comillas)
                body = json.dumps(payload)
                channel.basic_publish(exchange=exchange, routing_key=routing_key, body=body)
            except Exception as e:
                # Si falla la publicación, lo registramos y notificamos al usuario
                # No impedimos que la creación en Django continúe (decisión de diseño)
                messages.add_message(request, messages.WARNING, f'Item creado pero no fue posible notificar: {e}')
            finally:
                try:
                    connection.close()
                except Exception:
                    pass

            # --- RESPUESTA AL USUARIO (igual que antes)
            messages.add_message(request, messages.SUCCESS, 'Successfully created item')
            return HttpResponseRedirect(reverse('itemCreate'))
        else:
            print(form.errors)
    else:
        form = ItemForm()

    context = {
        'form': form,
    }
    return render(request, 'items/itemCreate.html', context)

