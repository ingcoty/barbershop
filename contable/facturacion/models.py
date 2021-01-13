from django.db import models
from django import forms

# Create your models here.
class Medidas(models.Model):
    id = models.AutoField(primary_key=True)
    unidad = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return "%s" % (self.unidad)


class Grupos(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return "%s" % (self.nombre)


class Producto(models.Model):
    id = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=20, unique=True)
    descripcion = models.CharField(max_length=100, unique=True)
    grupo = models.ForeignKey(Grupos, on_delete=models.PROTECT)
    impuesto = models.DecimalField(max_digits=10, decimal_places=2)
    medida = models.ForeignKey(Medidas, on_delete=models.PROTECT)
    costo = models.DecimalField(default=0, max_digits=10, decimal_places=2, blank=True)
    venta = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()


class TipoTercero(models.Model):
    id = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return "%s" % (self.tipo)

class TipoDocumentoTerceros(models.Model):
    id = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return "%s" % (self.tipo)

class TipoContribuyente(models.Model):
    id = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return "%s" % (self.tipo)

class Tercero(models.Model):
    id = models.AutoField(primary_key=True)
    tipodocumento = models.ForeignKey(TipoDocumentoTerceros, on_delete=models.PROTECT)
    codigo = models.CharField(max_length=20, unique=True, blank=True)
    nombre = models.CharField(max_length=50)
    tipotercero = models.ForeignKey(TipoTercero, on_delete=models.PROTECT)
    tipocontribuyente = models.ForeignKey(TipoContribuyente, on_delete=models.PROTECT)
    email = models.EmailField(blank=True, null=True)
    celular = models.IntegerField(blank=True)
    direccion = models.CharField(max_length=100, blank=True)
    ciudad = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return "%s" % (self.nombre)


class FormaPago(models.Model):
    id = models.AutoField(primary_key=True)
    fpago = models.CharField(max_length=20)


class TipoDocumento(models.Model):
    id = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=10)


class Documentos(models.Model):
    id = models.AutoField(primary_key=True)
    consecutivo = models.IntegerField()
    tipo = models.ForeignKey(TipoDocumento, on_delete=models.PROTECT)
    fecha = models.DateField()
    tercero = models.ForeignKey(Tercero, on_delete=models.PROTECT)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=10, decimal_places=2)
    impuesto = models.DecimalField(max_digits=10, decimal_places=2)
    neto = models.DecimalField(max_digits=10, decimal_places=2)
    fpago = models.ForeignKey(FormaPago, on_delete=models.PROTECT, null=True)
    relacion = models.CharField(max_length=20)
    user = models.CharField(max_length=30)
    estado = models.CharField(max_length=1, default=0)


class DocumentosDetalle(models.Model):
    id = models.AutoField(primary_key=True)
    numfac = models.ForeignKey(Documentos, on_delete=models.PROTECT)
    fecha = models.DateField()
    codproduct = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    descuento= models.DecimalField(max_digits=10, decimal_places=2)
    impuesto = models.DecimalField(max_digits=10, decimal_places=2)


class Inventario(models.Model):
    id = models.AutoField(primary_key=True)
    codproduct = models.ForeignKey(Producto, on_delete=models.PROTECT)
    existencia = models.IntegerField()
    fecha = models.DateField()
    numfac = models.ForeignKey(Documentos, on_delete=models.PROTECT)
    costo = models.DecimalField(max_digits=10, decimal_places=2)


class Empresa(models.Model):
    nombre = models.CharField(max_length=50)
    dir = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    cell = models.CharField(max_length=50, blank=True)
    resolucion = models.CharField(max_length=50, blank=True)
    ciudad = models.CharField(max_length=50)
    nit = models.CharField(max_length=50)