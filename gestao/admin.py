from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Cliente, Veiculo, OrdemServico, Produto, ItemOrdemServico


# 1. Configuração do Produto (Obrigatório para o autocomplete funcionar)
@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("nome", "estoque_atual", "preco_venda")
    search_fields = ["nome"]  # Isso permite que ele seja buscado em outros lugares


# 2. Configuração dos Itens dentro da OS
class ItemOrdemServicoInline(admin.TabularInline):
    model = ItemOrdemServico
    extra = 1
    # Agora o autocomplete_fields vai funcionar porque registramos o ProdutoAdmin com search_fields
    autocomplete_fields = ["produto"]
    fields = ("produto", "quantidade", "valor_unitario")


# 3. Configuração da Ordem de Serviço
@admin.register(OrdemServico)
class OrdemServicoAdmin(admin.ModelAdmin):
    # Campos que aparecem na listagem principal
    list_display = ("id", "veiculo", "status", "data_criacao",
                    "gerar_pdf_button")
    search_fields = ['nome']
    list_display_links = (
        "id",
        "veiculo",
    )  # Permite clicar no ID ou Veículo para editar

    # Habilita a edição dos itens (peças) na mesma tela da OS
    inlines = [ItemOrdemServicoInline]

    # Campos que não podem ser editados manualmente (o botão de impressão)
    readonly_fields = ("botao_pdf_detalhe",)

    # Botão de PDF na lista principal
    def gerar_pdf_button(self, obj):
        url = reverse("gerar_pdf_os", args=[obj.id])
        return format_html(
            '<a class="button" href="{}" target="_blank" style="background-color: #447e9b; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none;">📄 Gerar PDF</a>',
            url,
        )

    gerar_pdf_button.short_description = "Ações"

    # Botão de PDF dentro do formulário de edição
    def botao_pdf_detalhe(self, obj):
        if obj.id:
            url = reverse("gerar_pdf_os", args=[obj.id])
            return format_html(
                '<a href="{}" target="_blank" class="button" style="padding: 10px; background: #447e9b; color: white;">Imprimir OS Agora</a>',
                url,
            )
        return "Salve a OS primeiro para imprimir"

    botao_pdf_detalhe.short_description = "Impressão Rápida"


# 4. Registros dos outros modelos
admin.site.register(Cliente)
admin.site.register(Veiculo)
admin.site.register(ItemOrdemServico)  # Para visualizar itens isoladamente se precisar
