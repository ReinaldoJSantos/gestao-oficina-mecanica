from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    cpf = models.CharField(max_length=14, unique=True)

    def __str__(self):
        return self.nome


class Veiculo(models.Model):
    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE,
        related_name="veiculos"
    )
    placa = models.CharField(max_length=7, unique=True)
    modelo = models.CharField(max_length=50)
    marca = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.modelo} - {self.placa}"


class OrdemServico(models.Model):
    STATUS_CHOICES = [
        ("P", "Pendente"),
        ("A", "Aprovado"),
        ("F", "Finalizado"),
        ("C", "Cancelado"),  # Adicionei Cancelado para maior controle
    ]
    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE)
    mecanico = models.ForeignKey(User, on_delete=models.PROTECT)
    data_criacao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES,
                              default="P")
    observacoes = models.TextField(blank=True)

    def __str__(self):
        return f"OS {self.id} - {self.veiculo.placa}"

    # No model OrdemServico, mude para:


    @property
    def total_geral(self):
        return sum(item.subtotal for item in self.itens.all())


class Produto(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome da Peça/Produto")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição/Marca")
    preco_custo = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Preço de Custo"
    )
    preco_venda = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Preço de Venda"
    )
    estoque_atual = models.IntegerField(default=0, verbose_name="Estoque Atual")
    estoque_minimo = models.IntegerField(default=5, verbose_name="Estoque Mínimo")

    def __str__(self):
        return f"{self.nome} - R$ {self.preco_venda}"

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"


class ItemOrdemServico(models.Model):
    ordem_servico = models.ForeignKey(
        "OrdemServico", on_delete=models.CASCADE, related_name="itens"
    )
    produto = models.ForeignKey(
        "Produto",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Peça/Produto",
    )
    quantidade = models.PositiveIntegerField(default=1)
    valor_unitario = models.DecimalField(
        max_digits=10, decimal_places=2
    )  # Salva o preço no momento da venda

    @property
    def subtotal(self):
        return self.quantidade * self.valor_unitario

    def save(self, *args, **kwargs):
        # Se for a primeira vez salvando, puxa o preço de venda atual do produto
        if not self.valor_unitario:
            self.valor_unitario = self.produto.preco_venda
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome} na OS {self.ordem_servico.id}"


@receiver(post_save, sender=ItemOrdemServico)
def atualizar_estoque(sender, instance, created, **kwargs):
    if created and instance.produto:
        produto = instance.produto
        print(
            f"DEBUG: Descontando {instance.quantidade} de {produto.nome}"
        )  # Isso aparece no terminal
        produto.estoque_atual -= instance.quantidade
        produto.save()
