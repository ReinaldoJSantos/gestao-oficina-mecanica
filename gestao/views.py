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
from django.db.models import Q
from .forms import OrdemServicoForm
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle


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
        cpf = request.POST.get("cpf")
        Cliente.objects.create(
            nome=nome,
            email=email,
            cpf=cpf)
        return redirect("novo_cliente")
    return render(request, "gestao/form_cliente.html")


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


def gerar_pdf_os(request, os_id):
    os = OrdemServico.objects.get(pk=os_id)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="os_{os.id}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    largura, altura = A4

    # --- CABEÇALHO ---
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, altura - 50, f"ORDEM DE SERVIÇO Nº {os.id}")

    p.setFont("Helvetica", 12)
    p.drawString(100, altura - 80, f"Cliente: {os.veiculo.cliente.nome}")
    p.drawString(
        100, altura - 100, f"Veículo: {os.veiculo.modelo} ({os.veiculo.placa})"
    )
    p.drawString(
        100,
        altura - 120,
        f"Mecânico: {os.mecanico.get_full_name() or os.mecanico.username}",
    )
    p.drawString(100, altura - 140, f"Status: {os.get_status_display()}")
    p.drawString(
        100, altura - 160, f"Data: {os.data_criacao.strftime('%d/%m/%Y %H:%M')}"
    )

    # --- TABELA DE ITENS (PEÇAS/SERVIÇOS) ---
    p.setFont("Helvetica-Bold", 14)
    p.drawString(100, altura - 200, "Descrição dos Itens/Peças:")

    # Preparando os dados para a tabela
    dados_tabela = [["Produto/Peça", "Qtd", "V. Unit", "Subtotal"]]

    for item in os.itens.all():
        dados_tabela.append(
            [
                item.produto.nome if item.produto else "Serviço",
                str(item.quantidade),
                f"R$ {item.valor_unitario:.2f}",
                f"R$ {item.subtotal:.2f}",
            ]
        )

    # Adiciona a linha do Total Geral
    dados_tabela.append(["", "", "TOTAL GERAL:", f"R$ {os.total_geral:.2f}"])

    # Estilização da Tabela
    tabela = Table(dados_tabela, colWidths=[250, 50, 80, 80])
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                (
                    "BACKGROUND",
                    (0, -1),
                    (-1, -1),
                    colors.lightgrey,
                ),  # Fundo para o total
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    # Desenha a tabela no PDF
    tabela.wrapOn(p, largura, altura)
    tabela.drawOn(p, 50, altura - 230 - (len(dados_tabela) * 20))

    # --- OBSERVAÇÕES ---
    if os.observacoes:
        p.setFont("Helvetica-Oblique", 10)
        p.drawString(50, 100, "Observações:")
        p.drawString(50, 85, os.observacoes)

    p.showPage()
    p.save()
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


@login_required
def lista_clientes(request):
    busca = request.GET.get('search')

    if busca:
        # Filtra por nome ou cpf que contenha o termo buscado
        clientes = Cliente.objects.filter(
            Q(nome__icontains=busca) | Q(cpf__icontains=busca)
        ).order_by('nome')
    else:
        clientes = Cliente.objects.all().order_by('nome')

    return render(request, 'gestao/lista_clientes.html', {
        'clientes': clientes,
        'busca': busca
    })


@login_required
def salvar_cliente(request, pk=None):
    # Se houver um pk, busca o cliente para editar, senão cria um novo
    cliente = get_object_or_404(Cliente, pk=pk) if pk else None

    if request.method == 'POST':
        nome = request.POST.get('nome'),
        email = request.POST.get('email')
        telefone = request.POST.get('telefone'),
        cpf = request.POST.get('cpf')

        if cliente:
            # Atualiza cliente existente
            cliente.nome = nome
            cliente.email = email
            cliente.telefone = telefone
            cliente.cpf = cpf
            cliente.save()
        else:
            # Cria novo cliente
            Cliente.objects.create(
                nome=nome,
                email=email,
                telefone=telefone,
                cpf=cpf
            )
        return redirect('lista_clientes')
    return render(request, 'gestao/form_cliente.html', {
        'cliente': cliente
    })


@login_required
def excluir_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == 'POST':
        cliente.delete()

        return ('lista_clientes')
    return render(request, 'gestao/confirmar_exclusao.html', {
        'obj': cliente,
        'tipo': 'Cliente'
    })


@login_required
def lista_veiculos(request):
    busca = request.GET.get("search")
    if busca:
        # Filtra pela placa ou modelo do carro
        veiculos = Veiculo.objects.filter(
            Q(placa__icontains=busca) | Q(modelo__icontains=busca)
        ).order_by("modelo")
    else:
        veiculos = Veiculo.objects.all().order_by("placa")

    return render(
        request, "gestao/lista_veiculos.html", {
            "veiculos": veiculos,
            "busca": busca}
    )


@login_required
def salvar_veiculo(request, pk):
    # Se houver um pk busca o veiculo para editar, senão cria um novo
    veiculo = get_object_or_404(Veiculo, pk=pk) if pk else None

    # IMPORTANTE: Pegar todos os clientes para o dropdown
    clientes = Cliente.objects.all().order_by("nome")

    if request.method == 'POST':
        placa = request.POST.get('placa')
        modelo = request.POST.get('modelo')
        marca = request.POST.get('marca')

        if veiculo:
            veiculo.placa = placa
            veiculo.modelo = modelo
            veiculo.marca = marca
            veiculo.save()

        else:
            # Cria novo veiculo
            veiculo.objects.create(
                placa=placa,
                modelo=modelo,
                marca=marca
            )
        return redirect('lista_veiculos')
    return render(
        request,
        "gestao/form_veiculo.html",
        {"veiculo": veiculo, "clientes": clientes},  # Envia para o HTML
    )


@login_required
def excluir_veiculo(request, pk):
    veiculo = get_object_or_404(Veiculo, pk=pk)

    if request.method == 'POST':
        veiculo.delete()
        return ('lista_veiculos')
    return render(request, 'gestao/confirmar_exclusao.html', {
        'obj': veiculo,
        'tipo': veiculo
    })


@login_required
def editar_os(request, pk):
    # 1. Busca a Os existente ou dar erro 404 se não encontrar
    os = get_object_or_404(OrdemServico, pk=pk)

    if request.method == 'POST':
    # 2. O 'instance=os' Ele diz ao Django para atualizar a OS, e  não criar uma nova

        form = OrdemServicoForm(request.POST, instance=os)
        if form.get_is_valid():
            form.save()

            return redirect('historico_veiculo')
        else:
            # 3. No GET, ele carrega o form já preenchido com os dados atuais
            form = OrdemServicoForm(instance=os)
        return render(request, 'gestao/form_os.html', {
            'form': form,
            'os': os
        })
