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



def item_create(request):
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            # 1) Intentamos crear usando create_item (si devuelve instancia, perfecto)
            item = None
            try:
                item = create_item(form)  # preferimos que esta función retorne la instancia creada
            except Exception as e:
                # Si create_item falla, registramos y continuamos con intentos alternativos
                messages.add_message(request, messages.WARNING, f'Warning al crear con create_item: {e}')

            # 2) Si no hay instancia y el form es ModelForm, intentamos form.save()
            if item is None and hasattr(form, 'save'):
                try:
                    item = form.save()
                except Exception as e:
                    # si usar form.save() no es posible, lo ignoramos y seguiremos con cleaned_data
                    messages.add_message(request, messages.DEBUG, f'form.save() no ejecutado: {e}')

            # 3) Ahora armamos payload_data con preferencia a los atributos de item,
            # si no están, usamos form.cleaned_data como fallback.
            payload_data = {}
            if item is not None:
                # intenta extraer los campos más comunes; adapta los nombres a tu modelo
                payload_data['id'] = getattr(item, 'id', None)
                payload_data['name'] = getattr(item, 'name', None)
                # si tienes campos de usuario/creator:
                creator = getattr(item, 'created_by', None) or getattr(item, 'creator', None)
                payload_data['created_by'] = str(creator) if creator is not None else None
                # añade otros campos que quieras:
                # payload_data['other'] = getattr(item, 'other_field', None)
            else:
                # fallback a cleaned_data (valores del form)
                cd = form.cleaned_data
                # extrae campos seguros que existan
                payload_data['id'] = cd.get('id') if 'id' in cd else None
                payload_data['name'] = cd.get('name') if 'name' in cd else cd.get('titulo') if 'titulo' in cd else None
                payload_data['created_by'] = cd.get('created_by') if 'created_by' in cd else None
                # añade demás campos según tu formulario

            # --- Construir payload estándar
            payload = {
                'action': 'created',
                'model': 'Item',
                'data': payload_data
            }

            # --- PUBLICAR EN RABBITMQ (import perezoso)
            try:
                import pika
            except ImportError:
                messages.add_message(request, messages.WARNING,
                                     'Item creado pero la librería "pika" no está instalada; no se pudo notificar via RabbitMQ.')
            else:
                rabbit_host = getattr(settings, "RABBIT_HOST", os.environ.get("RABBIT_HOST", "127.0.0.1"))
                rabbit_user = getattr(settings, "RABBIT_USER", os.environ.get("RABBIT_USER", "monitoring_user"))
                rabbit_password = getattr(settings, "RABBIT_PASSWORD", os.environ.get("RABBIT_PASSWORD", "isis2503"))
                exchange = getattr(settings, "RABBIT_EXCHANGE", os.environ.get("RABBIT_EXCHANGE", "monitoring_measurements"))
                routing_key = getattr(settings, "RABBIT_ROUTING_KEY", os.environ.get("RABBIT_ROUTING_KEY", "ML.505.Item"))

                try:
                    credentials = pika.PlainCredentials(rabbit_user, rabbit_password)
                    params = pika.ConnectionParameters(host=rabbit_host, credentials=credentials)
                    connection = pika.BlockingConnection(params)
                    channel = connection.channel()
                    channel.exchange_declare(exchange=exchange, exchange_type='topic', durable=False)
                    body = json.dumps(payload)
                    channel.basic_publish(exchange=exchange, routing_key=routing_key, body=body)
                except Exception as e:
                    messages.add_message(request, messages.WARNING, f'Item creado pero no fue posible notificar: {e}')
                finally:
                    try:
                        connection.close()
                    except Exception:
                        pass

            messages.add_message(request, messages.SUCCESS, 'Successfully created item')
            return HttpResponseRedirect(reverse('itemCreate'))
        else:
            print(form.errors)
    else:
        form = ItemForm()

    return render(request, 'items/itemCreate.html', {'form': form})

def item_list(request):
    items = get_items()
    context = {
        'item_list': items
    }
    return render(request, 'items/items.html', context)
