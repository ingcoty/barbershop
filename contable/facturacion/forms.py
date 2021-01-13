from django import forms
from .models import *

class frmProducto(forms.ModelForm):
    class Meta:
        model = Producto
        fields =  '__all__'

class frmGrupo(forms.ModelForm):
    class Meta:
        model = Grupos
        fields =  '__all__'

class frmUnidades(forms.ModelForm):
    class Meta:
        model = Medidas
        fields =  '__all__'

class frmTercero(forms.ModelForm):
    class Meta:
        model = Tercero
        fields =  '__all__'

class frmTipoTercero(forms.ModelForm):
    class Meta:
        model = TipoTercero
        fields =  '__all__'

class frmTipoContribuyente(forms.ModelForm):
    class Meta:
        model = TipoContribuyente
        fields =  '__all__'