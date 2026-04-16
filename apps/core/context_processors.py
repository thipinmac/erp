"""Context processors globais."""


def tenant_info(request):
    """Disponibiliza empresa e filial em todos os templates."""
    return {
        "empresa_ativa": getattr(request, "empresa", None),
        "filial_ativa": getattr(request, "filial", None),
    }


def menu_items(request):
    """Menu lateral do sistema."""
    if not request.user.is_authenticated:
        return {"menu_items": []}

    items = [
        {
            "label": "Dashboard",
            "url_name": "bi:dashboard",
            "icon": "chart-bar",
            "modulo": "bi",
        },
        {
            "label": "CRM",
            "icon": "users",
            "modulo": "crm",
            "filhos": [
                {"label": "Pipeline", "url_name": "crm:pipeline"},
                {"label": "Leads", "url_name": "crm:lead_list"},
                {"label": "Visitas", "url_name": "crm:visita_list"},
            ],
        },
        {
            "label": "Orçamentos",
            "icon": "calculator",
            "modulo": "orcamentos",
            "filhos": [
                {"label": "Todos", "url_name": "orcamentos:list"},
                {"label": "Novo rápido", "url_name": "orcamentos:rapido_create"},
                {"label": "Novo técnico", "url_name": "orcamentos:tecnico_create"},
            ],
        },
        {
            "label": "Pedidos",
            "url_name": "pedidos:kanban",
            "icon": "clipboard-list",
            "modulo": "pedidos",
        },
        {
            "label": "Contratos",
            "url_name": "contratos:list",
            "icon": "document-text",
            "modulo": "contratos",
        },
        {
            "label": "Engenharia",
            "icon": "cog",
            "modulo": "engenharia",
            "filhos": [
                {"label": "Projetos", "url_name": "engenharia:projeto_list"},
                {"label": "BOM", "url_name": "engenharia:bom_list"},
            ],
        },
        {
            "label": "Compras",
            "url_name": "compras:list",
            "icon": "shopping-cart",
            "modulo": "compras",
        },
        {
            "label": "Estoque",
            "url_name": "estoque:list",
            "icon": "archive",
            "modulo": "estoque",
        },
        {
            "label": "Produção (PCP)",
            "url_name": "producao:kanban",
            "icon": "chip",
            "modulo": "producao",
        },
        {
            "label": "Entregas",
            "url_name": "entrega:agenda",
            "icon": "truck",
            "modulo": "entrega",
        },
        {
            "label": "Assistência",
            "url_name": "assistencia:list",
            "icon": "wrench-screwdriver",
            "modulo": "assistencia",
        },
        {
            "label": "Financeiro",
            "icon": "banknotes",
            "modulo": "financeiro",
            "filhos": [
                {"label": "Contas a Receber", "url_name": "financeiro:receber"},
                {"label": "Contas a Pagar", "url_name": "financeiro:pagar"},
                {"label": "DRE", "url_name": "financeiro:dre"},
            ],
        },
        {
            "label": "Fiscal",
            "url_name": "fiscal:list",
            "icon": "receipt-tax",
            "modulo": "fiscal",
        },
        {
            "label": "Cadastros",
            "icon": "database",
            "modulo": "cadastros",
            "filhos": [
                {"label": "Clientes", "url_name": "cadastros:cliente_list"},
                {"label": "Fornecedores", "url_name": "cadastros:fornecedor_list"},
                {"label": "Itens/Materiais", "url_name": "cadastros:item_list"},
            ],
        },
        {
            "label": "Configurações",
            "url_name": "administracao:config",
            "icon": "adjustments-horizontal",
            "modulo": "administracao",
            "admin_only": True,
        },
    ]

    return {"menu_items": items}
