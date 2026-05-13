BRAZIL_STATES = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AP": "Amapa",
    "AM": "Amazonas",
    "BA": "Bahia",
    "CE": "Ceara",
    "DF": "Distrito Federal",
    "ES": "Espirito Santo",
    "GO": "Goias",
    "MA": "Maranhao",
    "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais",
    "PA": "Para",
    "PB": "Paraiba",
    "PR": "Parana",
    "PE": "Pernambuco",
    "PI": "Piaui",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul",
    "RO": "Rondonia",
    "RR": "Roraima",
    "SC": "Santa Catarina",
    "SP": "Sao Paulo",
    "SE": "Sergipe",
    "TO": "Tocantins",
}

RISK_ACTIONS = {
    "bajo": [
        "Mantener flujo logistico normal.",
        "Monitorear solo por reglas operativas estandar.",
    ],
    "medio": [
        "Revisar ruta, vendedor y promesa de entrega.",
        "Confirmar despacho si existen pedidos similares acumulados.",
        "Preparar comunicacion preventiva si el cliente es sensible al plazo.",
    ],
    "alto": [
        "Priorizar seguimiento logistico antes del corte operativo.",
        "Validar despacho con el vendedor y transportista.",
        "Escalar si la ruta aparece repetidamente en la cola de riesgo.",
        "Preparar comunicacion proactiva al cliente.",
    ],
}


def normalize_state_code(value: str | None) -> str:
    if not value:
        return ""
    return value.strip().upper()


def state_name(code: str | None) -> str:
    normalized = normalize_state_code(code)
    return BRAZIL_STATES.get(normalized, "Desconocido")


def state_label(code: str | None) -> str:
    normalized = normalize_state_code(code)
    if not normalized:
        return "Desconocido"
    return f"{normalized} - {state_name(normalized)}"


def code_from_state_label(label: str) -> str:
    return normalize_state_code(label.split(" - ", 1)[0])


def state_catalog(codes: list[str] | None = None) -> list[dict]:
    selected_codes = sorted(codes or BRAZIL_STATES.keys())
    return [
        {
            "code": normalize_state_code(code),
            "name": state_name(code),
            "label": state_label(code),
        }
        for code in selected_codes
    ]


def recommendation_for(level: str) -> str:
    normalized = level.strip().lower()
    actions = RISK_ACTIONS[normalized]
    return " ".join(actions)


def actions_for(level: str) -> list[str]:
    return RISK_ACTIONS[level.strip().lower()]
