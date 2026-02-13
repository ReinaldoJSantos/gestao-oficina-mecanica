from django import forms
from .models import OrdemServico, ItemServico


class OSForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = ["veiculo", "status", "observacoes"]
        # Usamos widgets para deixar o visual do Bootstrap mais bonito
        widgets = {
            "observacoes": forms.Textarea(attrs={"rows": 3}),
        }


# O inlineformset permite adicionar vários itens (peças) na mesma tela da OS
ItemServicoFormSet = forms.inlineformset_factory(
    OrdemServico,
    ItemServico,
    fields=["descricao", "quantidade", "valor_unitario"],
    extra=1,  # Quantidade de linhas vazias que aparecem inicialmente
    can_delete=True,
)
