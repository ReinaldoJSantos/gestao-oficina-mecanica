from django.core.mail import EmailMessage
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from .models import (
    Cliente,
    OrdemServico,
    ItemOrdemServico,
    Veiculo,
)
from django.db import transaction

from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML


@login_required
def dashboard(request):
    # 1. Conta quantas OS existem por status
    resumo_status = OrdemServico.objects.values(
        "status").annotate(total=Count("id"))

    # 2. Busca todas as OS
    todas_os = OrdemServico.objects.all()

    # 3. Calcula o faturamento total usando a property que criamos
    # Somamos o total_geral de cada OS que está no banco
    valor_total = sum(os.total_geral for os in todas_os)

    # 4. (Opcional) Se quiser apenas o que está PENDENTE:
    # valor_pendente = sum(os.total_geral for os in todas_os
    # if os.status == 'P')

    ultimas_os = todas_os.order_by("-data_criacao")[:5]

    return render(
        request,
        "gestao/dashboard.html",
        {
            "ultimas_os": ultimas_os,
            "resumo": resumo_status,
            "valor_total": valor_total,  # Agora a variável vai com valor real!
        },
    )


# View simples para cadastrar Cliente
def novo_cliente(request):
    if request.method == "POST":
        nome = request.POST.get("nome")
        email = request.POST.get("email")
        cpf = request.POST.GET("CPF")
        Cliente.object.create(nome=nome,
                              email=email, cpf=cpf)
        return redirect("novo_veiculo")
    return render(request, "gestao/form_clinete.html")


# View simples para cadastrar veiculo


def novo_veiculo(request):
    clientes = Cliente.objects.all()
    if request.method == "POST":
        cliente_id = request.POST.get("cliente")
        cliente = Cliente.objects.get(id=cliente_id)
        Veiculo.objects.create(
            cliente=cliente,
            placa=request.POST.get("placa"),
            modelo=request.POST.get("modelo"),
            marca=request.POST.get("marca"),
        )
        return redirect("nova_os")
    return render(request, "gestao/form_veiculo.html", {"clientes": clientes})


@login_required
def gerar_pdf_os(request, pk):
    os = get_object_or_404(OrdemServico, pk=pk)
    html_string = render_to_string("gestao/orcamento_pdf.html", {"os": os})

    html = HTML(string=html_string)
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")

    # Criamos um nome de arquivo dinâmico e limpo
    data_formatada = os.data_criacao.strftime('%Y%m%d')
    nome_arquivo = f"OS_{os.id}_{os.veiculo.placa}_{data_formatada}.pdf"
    response["Content-Disposition"] = f'inline; filename="{nome_arquivo}"'

    return response


@login_required
def historico_veiculo(request):
    placa = request.GET.get('placa')

    if placa:
        # Se digitou a placa, filtra só por ela
        ordens = OrdemServico.objects.filter(
            veiculo__placa__iexact=placa).order_by('-data_criacao')
    else:
        # Se não digitou nada, mostra as 10 mais recentes do sistema todo
        ordens = OrdemServico.objects.all().order_by('-data_criacao')[:10]

    return render(request, 'gestao/historico.html', {'ordens': ordens,
                                                     'placa': placa})


@login_required
def nova_os(request, pk=None):
    # Se houver PK, estamos editando. Se não, estamos criando.
    os_instancia = get_object_or_404(OrdemServico, pk=pk) if pk else None

    if request.method == "POST":
        # 1. Pegamos os dados básicos da OS
        veiculo_id = request.POST.get("veiculo")
        veiculo = get_object_or_404(Veiculo, id=veiculo_id)
        status = request.POST.get("status", "P")
        observacoes = request.POST.get("observacoes", "")

        # 2. Criamos ou Atualizamos a OS
        if os_instancia:
            os_instancia.veiculo = veiculo
            os_instancia.status = status
            os_instancia.observacoes = observacoes
            os_instancia.save()
            # Se for edição, talvez você queira limpar os itens antigos antes
            # de re-adicionar
            os_instancia.itens.all().delete()
            os = os_instancia
        else:
            os = OrdemServico.objects.create(
                veiculo=veiculo,
                status=status,
                observacoes=observacoes,
                mecanico=request.user,
            )

        # 3. Processamos os Itens (vêm do formulário dinâmico)
        descricoes = request.POST.getlist("descricao[]")
        quantidades = request.POST.getlist("quantidade[]")
        valores = request.POST.getlist("valor[]")

        for desc, qtd, val in zip(descricoes, quantidades, valores):
            if desc:  # Só salva se tiver descrição
                ItemOrdemServico.objects.create(
                    ordem_servico=os,
                    descricao=desc,
                    quantidade=float(qtd.replace(",", ".")),
                    valor_unitario=float(val.replace(",", ".")),
                )

        messages.success(request, "Ordem de Serviço salva com sucesso!")
        return redirect("historico_veiculo")

    # Se for GET, apenas mostra o formulário
    veiculos = Veiculo.objects.all()
    return render(
        request, "gestao/form_os.html", {"veiculos": veiculos,
                                         "os": os_instancia}
    )


@login_required
def enviar_orcamento_email(request, pk):
    os = get_object_or_404(OrdemServico, pk=pk)

    # 1. Geramos o PDF
    html_string = render_to_string("gestao/orcamento_pdf.html", {"os": os})
    pdf = HTML(string=html_string).write_pdf()

    # 2. Criamos o objeto de e-mail com argumentos nomeados (Seguro!)
    email = EmailMessage(
        subject=f"Orçamento de Manutenção - OS {os.id} - {os.veiculo.modelo}",
        body=f"Olá {os.veiculo.cliente.nome},\n\nSegue em anexo o orçamento detalhado para o veículo {os.veiculo.modelo}.\n\nFicamos no aguardo da sua aprovação.",
        from_email="reinaldo.rsmaster@gmail.com",  # O e-mail configurado no settings.py
        to=[os.veiculo.cliente.email],  # Deve ser uma LISTA []
    )

    # 3. Anexamos o PDF
    email.attach(f"Orcamento_{os.id}.pdf", pdf, "application/pdf")

    try:
        email.send()
        messages.success(
            request,
            f"E-mail enviado com sucesso para {os.veiculo.cliente.email}!"
        )
    except Exception as e:
        messages.error(request, f"Erro técnico ao enviar: {e}")

    return redirect("historico_veiculo")


def detalhe_os(request, pk):
    # O get_object_or_404 é uma boa prática para evitar erros 500
    os = get_object_or_404(OrdemServico, pk=pk)
    return render(request, "gestao/detalhe_os.html", {"os": os})


@login_required
def salvar_os(request, pk=None):
    # Se tiver pk, estamos editando. Se não, estamos criando uma nova.
    os_instancia = get_object_or_404(OrdemServico, pk=pk) if pk else None
    veiculos = Veiculo.objects.all()

    if request.method == "POST":
        veiculo_id = request.POST.get("veiculo")
        status = request.POST.get("status")
        observacoes = request.POST.get("observacoes")

        veiculo = get_object_or_404(Veiculo, id=veiculo_id)

        # Usamos uma transação para garantir que se der erro nos itens,
        # não salve a OS
        with transaction.atomic():
            if os_instancia:
                # Editando OS existente
                os_instancia.veiculo = veiculo
                os_instancia.status = status
                os_instancia.observacoes = observacoes
                os_instancia.save()
                # Limpamos os itens antigos para re-salvar os novos
                # (lógica mais simples)
                os_instancia.itens.all().delete()
                os = os_instancia
            else:
                # Criando Nova OS
                os = OrdemServico.objects.create(
                    veiculo=veiculo,
                    mecanico=request.user,
                    status=status,
                    observacoes=observacoes,
                )

            # Salvando os Itens (Peças/Serviços)
            descricoes = request.POST.getlist("descricao[]")
            quantidades = request.POST.getlist("quantidade[]")
            valores = request.POST.getlist("valor[]")

            for desc, qtd, val in zip(descricoes, quantidades, valores):
                if desc:
                    # Limpeza de valores para garantir o formato decimal
                    valor_limpo = val.replace(".", "").replace(",", ".")
                    ItemOrdemServico.objects.create(
                        ordem_servico=os,
                        descricao=desc,
                        quantidade=float(qtd.replace(",", ".")),
                        valor_unitario=float(valor_limpo),
                    )

        return redirect("detalhe_os", pk=os.id)

    return render(
        request, "gestao/form_os.html", {"os": os_instancia,
                                         "veiculos": veiculos}
    )


@login_required
def excluir_os(request, pk):
    os = get_object_or_404(
        OrdemServico,
        pk=pk
    )

    if request.method == 'POST':
        os.delete()
        return redirect('dashboard')
    return render(request, 'gestao/confirmar_exclusao.html', {
        'obj': os,
        'tipo': 'Orem de serviço'
    })