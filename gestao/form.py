from django import forms
from .models import OrdemServico


class OrdemServicoForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        # Os campos que você me passou:
        fields = ["veiculo", "mecanico", "status", "observacoes"]

        # O Django permite "embelezar" os campos aqui mesmo
        widgets = {
            "veiculo": forms.Select(attrs={"class": "form-select"}),
            "mecanico": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "observacoes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Detalhes do defeito...",
                }
            ),
        }
        labels = {
            "veiculo": "Veículo do Cliente",
            "mecanico": "Mecânico Responsável",
            "status": "Status da OS",
            "observacoes": "Observações Técnicas",
        }
