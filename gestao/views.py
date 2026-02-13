from django.shortcuts import render, redirect, get_object_or_404
from .forms import OSForm, ItemServicoFormSet
from .models import OrdemServico


def historico_veiculo(request):
    # 1. Pegamos a placa que o usuário digitou na busca (via método GET)
    placa_buscada = request.GET.get("placa")
    ordens = []

    if placa_buscada:
        # 2. Buscamos todas as ordens de serviço dessa placa
        # Usamos __iexact para ignorar maiúsculas/minúsculas
        ordens = OrdemServico.objects.filter(
            veiculo__placa__iexact=placa_buscada
        ).order_status("-data_criacao")

    # 3. Mandamos o resultado para a tela (Template)
    return render(
        request, "gestao/historico.html", {"ordens": ordens, "placa": placa_buscada}
    )


def nova_os(request, pk=None):
    instance = get_object_or_404(OrdemServico, pk=pk) if pk else None

    if request.method == "POST":
        form = OSForm(request.POST, instance=instance)
        formset = ItemServicoFormSet(request.POST, instance=instance)

        if form.is_valid() and formset.is_valid():
            os_salva = form.save(commit=False)
            os_salva.mecanico = request.user
            os_salva.save()
            formset.instance = os_salva
            formset.save()
            return redirect("historico_veiculo")
    else:
        # Se for GET, apenas preparamos os formulários vazios ou com a instância
        form = OSForm(instance=instance)
        formset = ItemServicoFormSet(instance=instance)

    # ATENÇÃO: Este return deve estar FORA do 'if' e do 'else'.
    # Ele é a segurança de que a página sempre carregará algo.
    return render(request, "gestao/form_os.html", {"form": form, "formset": formset})
