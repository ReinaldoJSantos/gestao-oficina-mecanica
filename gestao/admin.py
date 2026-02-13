from django.contrib import admin
from .models import Cliente, Veiculo, OrdemServico, ItemServico


class ItemServicoInline(admin.TabularInline):
    model = ItemServico
    extra = 1  # Quantidade de linhas em branco para novos itens


@admin.register(OrdemServico)
class OrdemServicoAdmin(admin.ModelAdmin):
    list_display = ("id", "veiculo", "status", "data_criacao", "total_geral")
    list_filter = ("status", "data_criacao")
    search_fields = ("veiculo__placa", "veiculo__cliente__nome")
    inlines = [ItemServicoInline]


admin.site.register(Cliente)
admin.site.register(Veiculo)
