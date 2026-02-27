from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Cliente, Veiculo, OrdemServico, Produto, ItemOrdemServico


# Configuração dos Itens dentro da OS
class ItemOrdemServicoInline(admin.TabularInline):
    model = ItemOrdemServico
    extra = 1
    # Deixamos apenas os campos básicos para evitar erros de cálculo no admin
    fields = ('produto', 'quantidade', 'valor_unitario')


@admin.register(OrdemServico)
class OrdemServicoAdmin(admin.ModelAdmin):
    # Isso garante que você possa clicar no ID ou no Veículo para abrir a edição
    list_display = ('id', 'veiculo', 'status', 'data_criacao', 'gerar_pdf_button')

    # Habilita a edição dos itens na mesma tela
    inlines = [ItemOrdemServicoInline]

    def gerar_pdf_button(self, obj):
        # Aqui criamos o link para a sua view de PDF
        url = reverse("gerar_pdf_os", args=[obj.id])
        return format_html(
            '<a class="button" href="{}" target="_blank" style="background-color: #447e9b; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none;">📄 Gerar PDF</a>',
            url,
        )

    gerar_pdf_button.short_description = "Ações"  # Nome da coluna

    # Isso adiciona o botão no formulário de edição (opcional, mas muito útil)
    readonly_fields = ("botao_pdf_detalhe",)

    def botao_pdf_detalhe(self, obj):
        if obj.id:
            url = reverse("gerar_pdf_os", args=[obj.id])
            return format_html(
                '<a href="{}" target="_blank" class="button">Imprimir OS Agora</a>', url
            )
        return "Salve a OS primeiro para imprimir"

    botao_pdf_detalhe.short_description = "Impressão"

# Registros simples dos outros modelos
admin.site.register(Cliente)
admin.site.register(Veiculo)
admin.site.register(Produto)
admin.site.register(ItemOrdemServico) # Opcional, mas ajuda a ver se os itens estão lá
