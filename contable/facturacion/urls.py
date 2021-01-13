from django.urls import path
from django.contrib.auth import login, authenticate, logout
from .views import *

urlpatterns = [
    path('index', index, name='index'),
    path('productos/', productos, name='productos'),
    path('productos/editar/<int:id>/', editarproducto, name='editar'),
    path('productos/eliminar/<int:id>/', eliminarproducto, name='eliminar'),
    path('productos/frmproductos/<int:id>', formproductos, name='frmproductos'),
    path('productos/frmproductos/', newformproductos, name='newformproductos'),
    path('productos/tblproductos/', tblproductos, name='tblproductos'),
    path('productos/saveproducto/', saveproducto, name='saveproducto'),

    path('grupos/', grupos, name='grupos'),
    path('grupos/frmgrupos/', newformgrupos, name='newformgrupos'),
    path('grupos/frmgrupos/<int:id>', formgrupos, name='formgrupos'),
    path('grupos/tblgrupos/', tblgrupos, name='tblgrupos'),
    path('grupos/savegrupo/', savegrupo, name='savegrupo'),
    path('grupos/eliminar/<int:id>/', eliminargrupo, name='eliminargrupo'),
    path('grupos/editar/<int:id>/', editargrupo, name='editargrupo'),

    path('unidades/', unidades, name='undades'),
    path('unidades/frmunidades/', newformunidades, name='newformunidades'),
    path('unidades/frmunidades/<int:id>', formunidades, name='formunidades'),
    path('unidades/tblunidades/', tblunidades, name='tblunidades'),
    path('unidades/saveunidades/', saveunidades, name='saveunidades'),
    path('unidades/eliminar/<int:id>/', eliminarunidades, name='eliminarunidades'),
    path('unidades/editar/<int:id>/', editarunidades, name='editarunidades'),

    path('terceros/', terceros, name='terceros'),
    path('terceros/frmterceros/', newformterceros, name='newformterceros'),
    path('terceros/frmterceros/<int:id>', formterceros, name='formterceros'),
    path('terceros/tblterceros/', tblterceros, name='tblterceros'),
    path('terceros/saveterceros/', saveterceros, name='saveterceros'),
    path('terceros/editar/<int:id>/', editarterceros, name='editarterceros'),
    path('terceros/eliminar/<int:id>', eliminarterceros, name='eliminarterceros'),

    path('tipoterceros/', tipoterceros, name='tipoterceros'),
    path('tipoterceros/frmtipoterceros/', newformtipoterceros, name='newformtipoterceros'),
    path('tipoterceros/frmtipoterceros/<int:id>', formtipoterceros, name='formtipoterceros'),
    path('tipoterceros/tbltipoterceros/', tbltipoterceros, name='tbltipoterceros'),
    path('tipoterceros/savetipoterceros/', savetipoterceros, name='savetipoterceros'),
    path('tipoterceros/editar/<int:id>/', editartipoterceros, name='editartipoterceros'),
    path('tipoterceros/eliminar/<int:id>', eliminartipoterceros, name='eliminartipoterceros'),

    path('tipocontribuyente/', tipocontribuyente, name='tipocontribuyente'),
    path('tipocontribuyente/frmtipocontribuyente/', newformtipocontribuyente, name='newformtipocontribuyente'),
    path('tipocontribuyente/frmtipocontribuyente/<int:id>', formtipocontribuyente, name='formtipocontribuyente'),
    path('tipocontribuyente/tbltipocontribuyente/', tbltipocontribuyente, name='tbltipocontribuyente'),
    path('tipocontribuyente/savetipocontribuyente/', savetipocontribuyente, name='savetipocontribuyente'),
    path('tipocontribuyente/editar/<int:id>/', editartipocontribuyente, name='editartipocontribuyente'),
    path('tipocontribuyente/eliminar/<int:id>', eliminartipocontribuyente, name='eliminartipocontribuyente'),

    path('compras/factura/<int:num>', factura, name='facturacompra'),
    path('compras/', compras, name='compras'),
    path('transaccion/', transaccion, name='transaccion'),
    path('getTerceros/', getTerceros, name='getTerceros'),
    path('getProductos/', getProductos, name='getProductos'),
    path('facturarcompra/', facturarcompra, name='facturarcompra'),
    path('test/', test, name='test'),

    path('facturas/tblfacturascompras', tblfacturascompras, name='tblfacturascompras'),
    path('facturas/tblfacturasventas', tblfacturasventas, name='tblfacturasventas'),
    path('facturas/compras', facturascompras, name='facturascompras'),
    path('facturas/anular/<int:num>', anularcompra, name='anularcompra'),
    path('inventario/factura/<int:num>', factura, name='facturainventario'),
    path('inventario/', inventario, name='inventario'),
    path('inventario/tblinventario', tblinventario, name='tblinventario'),
    path('inventario/frminvetariodetalle/<int:num>', frminvetariodetalle, name='frmdetalle'),
    path('inventario/tbldetalle/<int:num>/<str:inicial>/<str:final>', tblinventariodetalle, name='tblinventariodetalle'),
    path('inventario/salidas', salidas, name='salidas_inventario'),
    path('inventario/salidaproducto/', salidaproducto, name='salidaproducto'),

    path('ventas/', ventas, name='ventas'),
    path('facturarventa/', facturarventa, name='facturarventa'),
    path('ventas/factura/<int:num>', factura, name='facturacompra'),
    path('facturas/ventas', facturasventas, name='facturasventas'),

    path('resumen', resumen, name='resumen'),
    path('ventas/existencia/<int:num>', existencia, name='existencia'),

    path('', login_, name='login_'),
    path('logout/', logout_, name='logout'),

    path('resumen/servicios', infservicio, name='infservicio'),
    path('resumen/ventas', infventas, name='infventas'),
    path('resumen/compras', infcompras, name='infcompras'),
    
    path('reportes/inventario', rptinventario, name='rptinventario'),
    path('reportes/ventas', rptventas, name='rptinventario'),
    
    path('reportes/tblRptInventario/<str:inicial>/<str:final>', tblRptInventario, name='tblrptinventario'),
    path('reportes/tblRptVentas/<str:inicial>/<str:final>', tblRptVentas, name='tblrptventas'),

    path('reportes/dowloadinventario/<str:inicial>/<str:final>', download_inventario, name='dowload_rptInventario'),
    path('reportes/dowloadventas/<str:inicial>/<str:final>', download_ventas, name='dowload_rptVentas'),
    

    #path('descargar/db', descargardb, name='decargardb'),
    

]