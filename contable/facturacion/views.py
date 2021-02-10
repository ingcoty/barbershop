import csv
import json
from django.core import paginator, serializers
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import connection
from django.http import FileResponse
from django.shortcuts import render, redirect
from django.db.models import Sum, Count
from .forms import *
from .models import *
from django.http import HttpResponse, request, JsonResponse
from django.contrib.auth import authenticate, logout, login
import datetime as datetime
from django.contrib.auth.decorators import login_required, permission_required
import os
import time


def sales_query(init_date, final_date, csv, grupo):
    with connection.cursor() as cursor:
        cursor.execute("create temp table base as select facturacion_documentosdetalle.fecha, sum(cantidad) as cantidad, codproduct_id, sum(facturacion_documentosdetalle.total) as total, user "
                       "from facturacion_documentosdetalle "
                       "left join facturacion_documentos "
                       "on numfac_id = facturacion_documentos.id "
                       "where tipo_id = '2' "
                       "and facturacion_documentosdetalle.fecha between %s and %s "
                       "group by user, codproduct_id", [init_date, final_date])

        cursor.execute("select base.fecha, base.cantidad, base.total, base.user, codproduct_id, facturacion_producto.descripcion "
                       "from base "
                       "join facturacion_producto "
                       "on base.codproduct_id = facturacion_producto.id "
                       "where facturacion_producto.grupo_id in ('1', '2') "
                       "order by base.user ")

        if csv == True:
            return cursor.fetchall()

        columns = [col[0] for col in cursor.description]
        ventas = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        cursor.execute("select base.user from base "
                       "join facturacion_producto "
                       "on base.codproduct_id = facturacion_producto.id "
                       "where facturacion_producto.grupo_id in ('1', '2') "
                       "group by user "
                       "order by user;")

        columns = [col[0] for col in cursor.description]
        users = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        return(ventas, users)


def inventory_query(init_date, final_date, csv):
    with connection.cursor() as cursor:
        cursor.execute("create temp table base as select id, codigo, descripcion, costo, venta "
                       "from facturacion_producto where grupo_id in ('1','3')")

        cursor.execute("create temp table init_inventory as select codproduct_id, sum(existencia) as existencia "
                       "from facturacion_inventario where fecha < %s "
                       "group by codproduct_id", [init_date])

        cursor.execute("create temp table temp1 as select id, codigo, descripcion, existencia as inicial, costo, venta "
                       "from base left join init_inventory on base.id = init_inventory.codproduct_id")

        cursor.execute("create temp table salidas as select codproduct_id, sum(existencia) as existencia "
                       "from facturacion_inventario where fecha >= %s and fecha <= %s "
                       "and existencia < 0 group by codproduct_id", [init_date, final_date])

        cursor.execute("create temp table temp2 as select id, codigo, descripcion, inicial, existencia as salidas, costo, venta "
                       "from temp1 left join salidas on id = salidas.codproduct_id")

        cursor.execute("create temp table entradas as select codproduct_id, sum(existencia) as entradas "
                       "from facturacion_inventario where fecha >= %s and fecha <= %s "
                       "and existencia > 0 group by codproduct_id", [init_date, final_date])

        cursor.execute("create temp table temp3 as select id, codigo, descripcion, inicial, salidas, entradas, costo, venta "
                       "from temp2 left join entradas on temp2.id = entradas.codproduct_id")

        cursor.execute("create temp table final_inventory as select codproduct_id, sum(existencia) as final "
                       "from facturacion_inventario where fecha <= %s group by codproduct_id", [final_date])

        cursor.execute("select id, codigo, descripcion, inicial, entradas, salidas, final, costo, venta, (venta-costo) as util "
                       "from temp3 left join final_inventory on temp3.id = final_inventory.codproduct_id")

        if csv == True:
            return cursor.fetchall()

        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]


@login_required(login_url="/")
def test(request):
    return render(request, 'facture/test.html')


# Create your views here.
@login_required(login_url="/")
def index(request):
    return render(request, 'facture/masterpage.html')


def resumen(request):
    os.environ['TZ'] = 'America/Bogota'
    time.tzset()
    productos = DocumentosDetalle.objects.filter(codproduct__grupo=1, numfac__estado=0, numfac__tipo=2,
                                                 fecha=datetime.date.today())
    ventas = 0
    numventas = 0
    for producto in productos:
        ventas += producto.total
        numventas += producto.cantidad

    servlist = DocumentosDetalle.objects.filter(codproduct__grupo=2, numfac__estado=0, numfac__tipo=2,
                                                fecha=datetime.date.today())
    servicios = 0
    numservicios = 0
    for servicio in servlist:
        servicios += servicio.total
        numservicios += servicio.cantidad

    compraslist = DocumentosDetalle.objects.filter(codproduct__grupo=1, numfac__estado=0, numfac__tipo=1,
                                                   fecha=datetime.date.today())
    compras = 0
    numcompras = 0
    for compra in compraslist:
        compras += compra.total
        numcompras += compra.cantidad

    context = {
        'ventas': ventas,
        'numventas': numventas,
        'servicios': servicios,
        'numservicios': numservicios,
        'compras': compras,
        'numcompras': numcompras,
        'total': ventas + servicios
    }
    return render(request, 'facture/resumen/resumen.html', context)


# vistas de productos
def productos(request):
    product = Producto.objects.all()
    context = {
        'items': product
    }
    return render(request, 'facture/productos/productos.html', context)


@login_required(login_url="/")
def saveproducto(request):
    form = frmProducto(request.POST)
    if form.is_valid():
        product = form.save()
        return JsonResponse(
            {'state': True, 'msg': 'Producto Registrado', 'id': product.id, 'descripcion': product.descripcion})
    else:
        return JsonResponse({'state': False, 'msg': 'Error en los datos'})


@login_required(login_url="/")
def newformproductos(request):
    form = frmProducto()
    context = {
        'form': form,
        'url_action': '/productos/saveproducto/'
    }
    return render(request, 'facture/forms/frmProductos.html', context)


@login_required(login_url="/")
def formproductos(request, id):
    product = Producto.objects.get(id=id)
    form = frmProducto(instance=product)
    context = {
        'form': form,
        'url_action': '/productos/editar/' + str(id) + '/'
    }
    return render(request, 'facture/forms/frmProductos.html', context)


@login_required(login_url="/")
def tblproductos(request):
    product = Producto.objects.all()
    context = {
        'items': product
    }
    return render(request, 'facture/tables/tblProductos.html', context)


@login_required(login_url="/")
def editarproducto(request, id):
    producto = Producto.objects.get(id=id)
    if request.method == 'POST':
        form = frmProducto(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            return JsonResponse({'state': True, 'msg': 'Cambios Realizados'})
        else:
            return JsonResponse({'state': False, 'msg': 'Producto con Movimiento'})


@login_required(login_url="/")
def eliminarproducto(request, id):
    producto = Producto.objects.get(id=id)
    try:
        producto.delete()
        return JsonResponse({'state': True, 'msg': 'Producto Eliminado'})
    except:
        return JsonResponse({'state': False, 'msg': 'Producto con Movimiento'})


# vistas de grupos
@login_required(login_url="/")
def grupos(request):
    return render(request, 'facture/productos/grupos.html')


@login_required(login_url="/")
def savegrupo(request):
    form = frmGrupo(request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({'state': True})
    else:
        return JsonResponse({'state': False})


@login_required(login_url="/")
def newformgrupos(request):
    form = frmGrupo()
    context = {
        'form': form,
        'url_action': '/grupos/savegrupo/'
    }
    return render(request, 'facture/forms/frmGrupos.html', context)


@login_required(login_url="/")
def formgrupos(request, id):
    group = Grupos.objects.get(id=id)
    form = frmGrupo(instance=group)
    context = {
        'form': form,
        'url_action': '/grupos/editar/' + str(id) + '/'
    }
    return render(request, 'facture/forms/frmGrupos.html', context)


@login_required(login_url="/")
def tblgrupos(request):
    group = Grupos.objects.all()
    context = {
        'items': group
    }
    return render(request, 'facture/tables/tblGrupos.html', context)


@login_required(login_url="/")
def editargrupo(request, id):
    group = Grupos.objects.get(id=id)
    if request.method == 'POST':
        form = frmGrupo(request.POST, instance=group)
        if form.is_valid():
            form.save()
            return JsonResponse({'state': True})
        else:
            return JsonResponse({'state': False})


@login_required(login_url="/")
def eliminargrupo(request, id):
    group = Grupos.objects.get(id=id)
    try:
        group.delete()
        return JsonResponse({'state': True, 'msg': 'Grupo Eliminado'})
    except:
        return JsonResponse({'state': False, 'msg': 'Grupo con Movimiento'})


# vistas de unidades
@login_required(login_url="/")
def unidades(request):
    return render(request, 'facture/productos/unidades.html')


@login_required(login_url="/")
def saveunidades(request):
    form = frmUnidades(request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({'state': True})
    else:
        return JsonResponse({'state': False})


@login_required(login_url="/")
def newformunidades(request):
    form = frmUnidades()
    context = {
        'form': form,
        'url_action': '/unidades/saveunidades/'
    }
    return render(request, 'facture/forms/frmUnidades.html', context)


@login_required(login_url="/")
def formunidades(request, id):
    obj = Medidas.objects.get(id=id)
    form = frmUnidades(instance=obj)
    context = {
        'form': form,
        'url_action': '/unidades/editar/' + str(id) + '/'
    }
    return render(request, 'facture/forms/frmUnidades.html', context)


@login_required(login_url="/")
def tblunidades(request):
    obj = Medidas.objects.all()
    context = {
        'items': obj
    }
    return render(request, 'facture/tables/tblUnidades.html', context)


@login_required(login_url="/")
def editarunidades(request, id):
    obj = Medidas.objects.get(id=id)
    if request.method == 'POST':
        form = frmUnidades(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return JsonResponse({'state': True, 'msg': 'Cambios Realizados'})
        else:
            return JsonResponse({'state': False, 'msg': 'Unidades con Movimiento'})


@login_required(login_url="/")
def eliminarunidades(request, id):
    obj = Medidas.objects.get(id=id)
    try:
        obj.delete()
        return JsonResponse({'state': True, 'msg': 'Unidad Eliminada'})
    except:
        return JsonResponse({'state': False, 'msg': 'Unidades con Movimiento'})


# vista de terceros
@login_required(login_url="/")
def terceros(request):
    return render(request, 'facture/terceros/terceros.html')


@login_required(login_url="/")
def newformterceros(request):
    form = frmTercero()
    context = {
        'form': form,
        'url_action': '/terceros/saveterceros/'
    }
    return render(request, 'facture/forms/frmTerceros.html', context)


@login_required(login_url="/")
def tblterceros(request):
    obj = Tercero.objects.all()
    context = {
        'items': obj
    }
    return render(request, 'facture/tables/tblTerceros.html', context)


@login_required(login_url="/")
def saveterceros(request):
    form = frmTercero(request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({'state': True})
    else:
        error_msg = []
        errors = json.loads(form.errors.as_json())
        for error in errors.keys():
            error_msg.append(errors[error][0]['message'])

        return JsonResponse({'state': False, 'errors': error_msg})


@login_required(login_url="/")
def formterceros(request, id):
    obj = Tercero.objects.get(id=id)
    form = frmTercero(instance=obj)
    context = {
        'form': form,
        'url_action': '/terceros/editar/' + str(id) + '/'
    }
    return render(request, 'facture/forms/frmTerceros.html', context)


@login_required(login_url="/")
def editarterceros(request, id):
    obj = Tercero.objects.get(id=id)
    if request.method == 'POST':
        form = frmTercero(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return JsonResponse({'state': True, 'msg': 'Cambios Realizados'})
        else:
            return JsonResponse({'state': False, 'msg': 'terceros con Movimiento'})


@login_required(login_url="/")
def eliminarterceros(request, id):
    obj = Tercero.objects.get(id=id)
    try:
        obj.delete()
        return JsonResponse({'state': True, 'msg': 'Unidad Eliminada'})
    except:
        return JsonResponse({'state': False, 'msg': 'terceros con Movimiento'})


# vista de tipos de terceros
@login_required(login_url="/")
def tipoterceros(request):
    return render(request, 'facture/terceros/tipoterceros.html')


@login_required(login_url="/")
def savetipoterceros(request):
    form = frmTipoTercero(request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({'state': True})
    else:
        return JsonResponse({'state': False})


@login_required(login_url="/")
def newformtipoterceros(request):
    form = frmTipoTercero()
    context = {
        'form': form,
        'url_action': '/tipoterceros/savetipoterceros/'
    }
    return render(request, 'facture/forms/frmTipoTerceros.html', context)


@login_required(login_url="/")
def formtipoterceros(request, id):
    obj = TipoTercero.objects.get(id=id)
    form = frmTipoTercero(instance=obj)
    context = {
        'form': form,
        'url_action': '/tipoterceros/editar/' + str(id) + '/'
    }
    return render(request, 'facture/forms/frmTipoTerceros.html', context)


@login_required(login_url="/")
def tbltipoterceros(request):
    obj = TipoTercero.objects.all()
    context = {
        'items': obj
    }
    return render(request, 'facture/tables/tblTipoTerceros.html', context)


@login_required(login_url="/")
def editartipoterceros(request, id):
    obj = TipoTercero.objects.get(id=id)
    if request.method == 'POST':
        form = frmTipoTercero(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return JsonResponse({'state': True, 'msg': 'Cambios Realizados'})
        else:
            return JsonResponse({'state': False, 'msg': 'Tipo de Tercero con Movimiento'})


@login_required(login_url="/")
def eliminartipoterceros(request, id):
    obj = TipoTercero.objects.get(id=id)
    try:
        obj.delete()
        return JsonResponse({'state': True, 'msg': 'Tipo de Tercero Eliminado'})
    except:
        return JsonResponse({'state': False, 'msg': 'Tipo de Tercero con Movimiento'})


# vista de tipos de contribuyente
@login_required(login_url="/")
def tipocontribuyente(request):
    return render(request, 'facture/terceros/tipocontribuyente.html')


@login_required(login_url="/")
def savetipocontribuyente(request):
    form = frmTipoContribuyente(request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({'state': True})
    else:
        return JsonResponse({'state': False})


@login_required(login_url="/")
def newformtipocontribuyente(request):
    form = frmTipoContribuyente()
    context = {
        'form': form,
        'url_action': '/tipocontribuyente/savetipocontribuyente/'
    }
    return render(request, 'facture/forms/frmTipoContribuyentes.html', context)


@login_required(login_url="/")
def formtipocontribuyente(request, id):
    obj = TipoContribuyente.objects.get(id=id)
    form = frmTipoContribuyente(instance=obj)
    context = {
        'form': form,
        'url_action': '/tipocontribuyente/editar/' + str(id) + '/'
    }
    return render(request, 'facture/forms/frmTipoContribuyentes.html', context)


@login_required(login_url="/")
def tbltipocontribuyente(request):
    obj = TipoContribuyente.objects.all()
    context = {
        'items': obj
    }
    return render(request, 'facture/tables/tblTipoContribuyentes.html', context)


@login_required(login_url="/")
def editartipocontribuyente(request, id):
    obj = TipoContribuyente.objects.get(id=id)
    if request.method == 'POST':
        form = frmTipoContribuyente(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return JsonResponse({'state': True, 'msg': 'Cambios Realizados'})
        else:
            return JsonResponse({'state': False, 'msg': 'Tipo de Contribuyente con Movimiento'})


@login_required(login_url="/")
def eliminartipocontribuyente(request, id):
    obj = TipoContribuyente.objects.get(id=id)
    try:
        obj.delete()
        return JsonResponse({'state': True, 'msg': 'Tipo de Contribuyente Eliminado'})
    except:
        return JsonResponse({'state': False, 'msg': 'Tipo de Contribuyente con Movimiento'})


# vista de facturación
@login_required(login_url="/")
def compras(request):
    # productos = Producto.objects.filter(~Q(id = 2))
    productos = Producto.objects.all()
    fpagos = FormaPago.objects.all()
    terceros = Tercero.objects.filter(tipotercero=1)
    numFactura = 0
    try:
        numFactura = Documentos.objects.all().order_by('-id')[0]
        numFactura = numFactura.id + 1
    except:
        print('no hay facturas')
    context = {
        'productos': productos,
        'numfactura': numFactura,
        'fpagos': fpagos,
        'terceros': terceros
    }
    return render(request, 'facture/transacciones/compras.html', context)


@login_required(login_url="/")
def transaccion(request):
    return redirect('/')


@login_required(login_url="/")
def getTerceros(request):
    terceros = Tercero.objects.all().values()
    terceros_list = list(terceros)
    return JsonResponse(terceros_list, safe=False)


@login_required(login_url="/")
def getProductos(request):
    productos = Producto.objects.all().values()
    productos_list = list(productos)
    return JsonResponse(productos_list, safe=False)


# actualizar el costo de los productos
def kardex(codigo):
    id = Producto.objects.get(codigo=codigo)
    products = Inventario.objects.filter(codproduct=id)
    cantidad = 0
    costo = 0

    for product in products:
        if product.costo > 0:
            cantidad += product.existencia
            costo += product.costo * product.existencia

    promedio = costo / cantidad
    id.costo = promedio
    id.save()


@login_required(login_url="/")
def facturarcompra(request):
    data = json.loads(request.POST.dict()['content'])
    consecutivo = Documentos.objects.filter(
        tipo=1).all().order_by('-consecutivo')
    if not consecutivo:
        consecutivo = 0
    else:
        consecutivo = consecutivo[0].consecutivo

    fecha = data['fecha']
    fecha = fecha[6:10] + '-' + fecha[0:2] + '-' + fecha[3:5]

    tipodoc = TipoDocumento.objects.get(id=1)

    factura = Documentos()
    factura.tipo = tipodoc
    factura.consecutivo = consecutivo + 1
    factura.fecha = fecha
    tercero = Tercero.objects.get(codigo=data['tercero'])
    factura.tercero = tercero
    factura.total = data['total']
    factura.descuento = data['descuento']
    factura.impuesto = data['impuesto']
    factura.neto = data['neto']
    fpago = FormaPago.objects.get(id=int(data['fpago']))
    factura.fpago = fpago
    factura.relacion = data['relacion']
    factura.user = request.user.get_full_name()
    factura.save()

    numFactura = Documentos.objects.filter(tipo=1).order_by('-id')[0]
    for product in data['productos']:
        detalle = DocumentosDetalle()
        detalle.numfac = numFactura
        detalle.codproduct = Producto.objects.get(codigo=product['codigo'])
        detalle.fecha = fecha
        detalle.cantidad = product['cantidad']
        detalle.valor = product['valor']
        detalle.descuento = product['descuento']
        detalle.impuesto = product['impuesto']
        detalle.total = product['total']
        detalle.save()
        inventario = Inventario()
        inventario.numfac = numFactura
        inventario.codproduct = Producto.objects.get(codigo=product['codigo'])
        inventario.fecha = fecha
        inventario.existencia = product['cantidad']
        inventario.costo = product['valor']
        inventario.save()
        kardex(product['codigo'])
    return JsonResponse({'state': True, 'factura_id': numFactura.id})


@login_required(login_url="/")
def factura(request, num):
    # data from enterprise
    info = Empresa.objects.get(id=1)
    fac = Documentos.objects.get(id=num)
    productos = DocumentosDetalle.objects.filter(numfac=num)
    context = {
        'empresa': info,
        'factura': fac,
        'productos': productos
    }
    return render(request, 'facture/transacciones/facCompra.html', context)


@login_required(login_url="/")
def anularcompra(request, num):
    # data from enterprise
    fac = Documentos.objects.get(id=num)
    fac.total = 0
    fac.descuento = 0
    fac.impuesto = 0
    fac.neto = 0
    fac.relacion = ''
    fac.estado = 1
    fac.save()

    inventory = Inventario.objects.filter(numfac=num)
    for product in inventory:
        product.existencia = 0
        product.costo = 0
        product.save()

    productos = DocumentosDetalle.objects.filter(numfac=num)
    for producto in productos:
        producto.valor = 0
        producto.total = 0
        producto.descuento = 0
        producto.impuesto = 0
        producto.save()

    return JsonResponse({'state': True, 'msg': 'factura anulada'})


@login_required(login_url="/")
# @permission_required('facturacion.delete_inventario', login_url="/blocked")
def facturascompras(request):
    return render(request, 'facture/compras/factura.html')




@login_required(login_url="/")
def tblfacturascompras(request):
    facturas = Documentos.objects.filter(tipo=1).order_by('-consecutivo')
    context = {
        'facturas': facturas
    }
    return render(request, 'facture/tables/tblFacturasCompras.html', context)


@login_required(login_url="/")
def facturasventas(request):
    facturas = Documentos.objects.filter(tipo=2).order_by('-consecutivo')
    page = request.GET.get('page', 1)
    paginator = Paginator(facturas, 20)
    try:
        facturas_pag = paginator.page(page)
    except PageNotAnInteger:
        facturas_pag = paginator.page(1)
    except EmptyPage:
        facturas_pag = paginator.page(paginator.num_pages)


    context = {
        'facturas': facturas_pag
    }
    return render(request, 'facture/ventas/factura.html', context)


@login_required(login_url="/")
def inventario(request):
    return render(request, 'facture/inventario/inventario.html')


@login_required(login_url="/")
def tblinventario(request):
    grupo = Inventario.objects.values('codproduct').annotate(Sum('existencia'))
    inventory = []
    for product in grupo:
        products = Producto.objects.get(id=product['codproduct'])
        inventory.append({'id': products.id, 'codigo': products.codigo, 'descripcion': products.descripcion,
                          'existencia': product['existencia__sum']})

    context = {
        'inventario': inventory
    }

    return render(request, 'facture/tables/tblInventario.html', context)


@login_required(login_url="/")
def frminvetariodetalle(request, num):
    detalles = Inventario.objects.filter(codproduct=num).first()
    context = {
        'productos': detalles
    }

    return render(request, 'facture/inventario/detallefrm.html', context)


@login_required(login_url="/")
def tblinventariodetalle(request, num, inicial, final):
    initdate = datetime.datetime.strptime(inicial, '%m-%d-%Y')
    enddate = datetime.datetime.strptime(final, '%m-%d-%Y')

    detalles = Inventario.objects.filter(
        codproduct=num, fecha__range=(initdate, enddate))
    context = {
        'productos': detalles
    }

    return render(request, 'facture/tables/tblInventarioDetalle.html', context)


@login_required(login_url="/")
def ventas(request):
    productos = Producto.objects.all()
    fpagos = FormaPago.objects.all()
    terceros = Tercero.objects.filter(tipotercero=2)
    context = {
        'productos': productos,
        'fpagos': fpagos,
        'terceros': terceros
    }
    return render(request, 'facture/transacciones/ventas.html', context)


@login_required(login_url="/")
def facturarventa(request):
    data = json.loads(request.POST.dict()['content'])
    consecutivo = Documentos.objects.filter(
        tipo=2).all().order_by('-consecutivo')
    if not consecutivo:
        consecutivo = 0
    else:
        consecutivo = consecutivo[0].consecutivo

    fecha = data['fecha']
    fecha = fecha[6:10] + '-' + fecha[0:2] + '-' + fecha[3:5]

    tipodoc = TipoDocumento.objects.get(id=2)

    factura = Documentos()
    factura.tipo = tipodoc
    factura.consecutivo = consecutivo + 1
    factura.fecha = fecha
    tercero = Tercero.objects.get(codigo=data['tercero'])
    factura.tercero = tercero
    factura.total = data['total']
    factura.descuento = data['descuento']
    factura.impuesto = data['impuesto']
    factura.neto = data['neto']
    fpago = FormaPago.objects.get(id=int(data['fpago']))
    factura.fpago = fpago
    factura.relacion = ''
    factura.user = request.user.get_full_name()
    factura.save()

    numFactura = Documentos.objects.filter(tipo=2).order_by('-id')[0]
    for product in data['productos']:
        detalle = DocumentosDetalle()
        detalle.numfac = numFactura
        prod = Producto.objects.get(codigo=product['codigo'])
        detalle.codproduct = prod
        detalle.fecha = fecha
        detalle.cantidad = product['cantidad']
        detalle.valor = product['valor']
        detalle.descuento = product['descuento']
        detalle.impuesto = product['impuesto']
        detalle.total = product['total']
        detalle.save()
        if prod.grupo.id == 1:
            inventario = Inventario()
            inventario.numfac = numFactura
            inventario.codproduct = Producto.objects.get(
                codigo=product['codigo'])
            inventario.fecha = fecha
            inventario.existencia = int(product['cantidad']) * -1
            inventario.costo = 0
            inventario.save()
    return JsonResponse({'state': True, 'factura_id': numFactura.id})


@login_required(login_url="/")
def existencia(request, num):
    productos = Inventario.objects.values(
        'codproduct').annotate(Sum('existencia'))
    stock = Producto.objects.get(id=num).stock
    existencia = 0
    for producto in productos:
        if producto['codproduct'] == num:
            existencia = producto['existencia__sum']

    return JsonResponse({'state': True, 'existencia': existencia, 'stock': stock})


def login_(request):
    if request.method == "GET" and not (request.user.is_authenticated):
        return render(request, 'facture/login/login.html')
    else:
        # validar el usuario
        if request.user.is_authenticated:
            return redirect('/index')
        else:
            username = request.POST.get('username', 'xxx')
            password = request.POST.get('password', 'xxx')
            user = authenticate(request, username=username, password=password)
            if user is None:
                arg = {}
                arg['message'] = 'Usuario o Contraseña incorrecta'
                return render(request, 'facture/login/login.html', arg)
            else:
                login(request, user)
                return redirect('/index')


@login_required(login_url="/")
def logout_(request):
    logout(request)
    return redirect('/')


@login_required(login_url="/")
def salidas(request):
    productos = Producto.objects.filter(grupo=1)
    terceros = Tercero.objects.filter(tipotercero=2)
    context = {
        'productos': productos,
        'terceros': terceros
    }

    return render(request, 'facture/inventario/salidas.html', context)


@login_required(login_url="/")
def salidaproducto(request):
    data = json.loads(request.POST.dict()['content'])
    consecutivo = Documentos.objects.filter(
        tipo=3).all().order_by('-consecutivo')
    if not consecutivo:
        consecutivo = 0
    else:
        consecutivo = consecutivo[0].consecutivo

    fecha = data['fecha']
    fecha = fecha[6:10] + '-' + fecha[0:2] + '-' + fecha[3:5]
    tipodoc = TipoDocumento.objects.get(id=3)
    factura = Documentos()
    factura.tipo = tipodoc
    factura.consecutivo = consecutivo + 1
    factura.fecha = fecha
    tercero = Tercero.objects.get(codigo=data['tercero'])
    factura.tercero = tercero
    factura.total = 0
    factura.descuento = 0
    factura.impuesto = 0
    factura.neto = 0
    factura.relacion = ''
    factura.user = request.user.get_full_name()
    factura.save()

    numFactura = Documentos.objects.filter(tipo=3).order_by('-id')[0]
    for product in data['productos']:
        detalle = DocumentosDetalle()
        detalle.numfac = numFactura
        detalle.codproduct = Producto.objects.get(codigo=product['codigo'])
        detalle.fecha = fecha
        detalle.cantidad = product['cantidad']
        detalle.valor = 0
        detalle.descuento = 0
        detalle.impuesto = 0
        detalle.total = 0
        detalle.save()
        inventory = Inventario()
        inventory.numfac = numFactura
        inventory.fecha = fecha
        inventory.codproduct = Producto.objects.get(codigo=product['codigo'])
        inventory.existencia = (int(product['cantidad']) * -1)
        inventory.costo = 0
        inventory.notes = product['motivo']
        inventory.save()

    return JsonResponse({'state': True, 'factura_id': numFactura.id})


@login_required(login_url="/")
def infservicio(request):
    os.environ['TZ'] = 'America/Bogota'
    time.tzset()
    servicios = DocumentosDetalle.objects.filter(codproduct__grupo=2, numfac__estado=0, numfac__tipo=2,
                                                 fecha=datetime.date.today()).order_by('-numfac__user')

    context = {
        'servicios': servicios
    }
    return render(request, 'facture/informes/infservicios.html', context)


def infventas(request):
    os.environ['TZ'] = 'America/Bogota'
    time.tzset()
    ventas = DocumentosDetalle.objects.filter(codproduct__grupo=1, numfac__estado=0, numfac__tipo=2,
                                              fecha=datetime.date.today()).order_by('-numfac__user')

    context = {
        'ventas': ventas
    }
    return render(request, 'facture/informes/infventas.html', context)


@login_required(login_url="/")
def infcompras(request):
    os.environ['TZ'] = 'America/Bogota'
    time.tzset()
    compras = DocumentosDetalle.objects.filter(numfac__estado=0, numfac__tipo=1,
                                               fecha=datetime.date.today()).order_by('-numfac__user')

    context = {
        'compras': compras
    }

    return render(request, 'facture/informes/infcompras.html', context)


@login_required(login_url="/")
def descargardb(request):
    db = open('db.sqlite3', 'rb')
    response = FileResponse(db)
    return response


def rptinventario(request):
    return render(request, 'facture/reportes/frmrptinventario.html')


def tblRptInventario(request, inicial, final):

    inicial = inicial[6:10] + '-' + inicial[0:2] + '-' + inicial[3:5]
    final = final[6:10] + '-' + final[0:2] + '-' + final[3:5]
    inventory = inventory_query(inicial, final, 0)

    for row in inventory:
        for key in row.keys():
            if row[key] is None:
                row[key] = 0

    info = Empresa.objects.get(id=1)
    context = {
        'fecha_inicial': inicial,
        'fecha_final': final,
        'empresa': info,
        'inventory': inventory
    }

    return render(request, 'facture/reportes/reporte_inventario.html', context)


def download_inventario(request, inicial, final):
    response = HttpResponse(content_type='txt/csv')
    response['Content-Disposition'] = "attachment; filename=inventory.csv"
    writer = csv.writer(response)
    writer.writerow(["Id", "Codigo", "Descripcion", "Inicial",
                     "Entradas", "Salidas", "Final", "Costo", "Venta", "Utilidad"])

    inventory = inventory_query(inicial, final, 1)
    for row in inventory:
        writer.writerow(row)

    return response


def rptventas(request):
    return render(request, 'facture/reportes/frmrptventas.html')


def tblRptVentas(request, inicial, final):

    inicial = inicial[6:10] + '-' + inicial[0:2] + '-' + inicial[3:5]
    final = final[6:10] + '-' + final[0:2] + '-' + final[3:5]
    products, users = sales_query(inicial, final, 0, 1)

    for row in products:
        for key in row.keys():
            if row[key] is None:
                row[key] = 0

    info = Empresa.objects.get(id=1)

    total = 0
    for product in products:
        total = total + float(product['total'])

    context = {
        'fecha_inicial': inicial,
        'fecha_final': final,
        'empresa': info,
        'products': products,
        'total': total
    }

    return render(request, 'facture/reportes/reporte_ventas.html', context)


def download_ventas(request, inicial, final):

    response = HttpResponse(content_type='txt/csv')
    response['Content-Disposition'] = "attachment; filename=sales.csv"
    writer = csv.writer(response)
    writer.writerow(["Fecha", "Cantidad", "Valor", "Prestador",
                     "Código", "Descripción"])

    sales = sales_query(inicial, final, 1, 0)
    for row in sales:
        writer.writerow(row)

    return response


def cal_costo(inicial, codproduct):
    with connection.cursor() as cursor:
        cursor.execute("select sum(existencia*costo)/sum(existencia) "
                       "as costo from facturacion_inventario where codproduct_id = %s "
                       "and existencia > 0 and fecha < %s", [codproduct, inicial])

        columns = [col[0] for col in cursor.description]
        response = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        return(response[0]['costo'])


def cal_cant(inicial, codproduct):
    with connection.cursor() as cursor:
        cursor.execute("select sum(existencia) as existencia from facturacion_inventario "
                       "where codproduct_id = %s "
                       "and fecha < %s", [codproduct, inicial])

        columns = [col[0] for col in cursor.description]
        response = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        return(response[0]['existencia'])


def kardex_table(initdate, finaldate, codproduct):
    with connection.cursor() as cursor:

        cursor.execute("create temp table resto as select facturacion_inventario.existencia, facturacion_inventario.fecha, "
                       "facturacion_inventario.costo, facturacion_tercero.nombre, facturacion_inventario.numfac_id as factura "
                       "from facturacion_inventario "
                       "inner join facturacion_documentos "
                       "on numfac_id = facturacion_documentos.id "
                       "inner join facturacion_tercero "
                       "on facturacion_documentos.tercero_id = facturacion_tercero.id "
                       "where codproduct_id = %s and facturacion_inventario.fecha > %s "
                       "and facturacion_inventario.fecha <= %s", [codproduct, initdate, finaldate])

        cursor.execute("select fecha, case when existencia > 0 then existencia "
                       "else 0 end as entradas, case when existencia < 0 then "
                       "existencia else 0 end as salidas, costo, nombre, factura from resto")

        columns = [col[0] for col in cursor.description]
        response = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        cant = round(cal_cant(initdate, codproduct), 1)
        costo = round(cal_costo(initdate, codproduct), 1)
        cantidad = cant
        costoacum = round(costo * cant, 1)
        costoprom = costo
        saldoAnt = costoacum
        init_row = {
            'fecha': initdate,
            'nombre': 'Saldo Inicial',
            'factura': 0,
            'cantAnterior': cant,
            'entradas': 0,
            'salidas': 0,
            'costo': costo,
            'costoProm': costoprom,
            'cantActual': cant,
            'salAnterior': costoacum,
            'salEntradas': 0,
            'salSalidas': 0,
            'salActual': costoacum
        }

        kardex_table = [init_row]

        for row in response:
            cantidad += row['entradas']
            row['cantAnterior'] = cant
            row['salAnterior'] = round(saldoAnt, 1)
            row['salEntradas'] = round(row['entradas'] * row['costo'], 1)
            cant = cant + row['entradas'] + row['salidas']
            saldoAnt
            row['cantActual'] = cant

            if row['entradas'] > 0:
                costoacum += row['costo'] * row['entradas']
                costoprom = costoacum/cantidad

            row['costoProm'] = round(costoprom, 1)
            row['salSalidas'] = round(-row['salidas'] * row['costoProm'], 1)
            row['salActual'] = round(
                row['salAnterior'] + row['salEntradas'] - row['salSalidas'], 1)
            saldoAnt = row['salActual']
            kardex_table.append(row)

        return(kardex_table)


def rptkardex(request):
    productos = Producto.objects.all()
    context = {
        'productos': productos
    }
    return render(request, 'facture/reportes/frmrptkardex.html', context)


def tblRptKardex(request, inicial, final, codproduct):
    inicial = inicial[6:10] + '-' + inicial[0:2] + '-' + inicial[3:5]
    final = final[6:10] + '-' + final[0:2] + '-' + final[3:5]
    table = kardex_table(inicial, final, codproduct)
    info = Empresa.objects.get(id=1)
    product = Producto.objects.get(id=codproduct)

    context = {
        'fecha_inicial': inicial,
        'fecha_final': final,
        'codigo': codproduct,
        'empresa': info,
        'producto': product,
        'kardex': table
    }

    return render(request, 'facture/reportes/reporte_kardex.html', context)


def download_kardex(request, inicial, final, codproduct):
    response = HttpResponse(content_type='txt/csv')
    producto = Producto.objects.filter(id=codproduct).values()    
    product_name = producto[0]['descripcion']
    response['Content-Disposition'] = "attachment; filename=" + product_name + ".csv"
    writer = csv.writer(response)

    writer.writerow([product_name])
    writer.writerow(["Fecha", "Tercero", "Factura", "Nacionalidad", "Compra",
                       "Costo", "Cantidad Anterior", "Entradas", "Salidas", "Cantidad Actual",
                       "Saldo Anterior", "Entradas", "Salidas", "Saldo Actual"])

    table = kardex_table(inicial, final, codproduct)
    for row in table:
        values = [
            row['fecha'],
            row['nombre'],
            row['factura'],
            "Salvadoreña",
            row['salEntradas'],
            row['costoProm'],
            row['cantAnterior'],
            row['entradas'],
            row['salidas'],
            row['cantActual'],
            row['salAnterior'],
            row['salEntradas'],
            row['salSalidas'],
            row['salActual'],
        ]
        writer.writerow(values)

    return response