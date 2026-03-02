"""
Informações de versão da API
"""

__version__ = "1.0.0"
__title__ = "Contract API"
__description__ = """
API para gerenciamento de contratos.

## Funcionalidades

* **Criar contratos** - Cria novos contratos no sistema
* **Cancelar contratos** - Cancela contratos existentes com validações de regras de negócio
* **Reprocessar contratos** - Reprocessa contratos com falha

## Regras de Negócio

* Contratos só podem ser cancelados dentro de 7 dias após criação
* Contratos só podem ser reprocessados após 5 minutos da última atualização
* Cancelamento requer idempotency key para prevenir duplicatas

## Changelog

### v1.0.0 (2026-03-01)
- Endpoint de criação de contratos
- Endpoint de cancelamento de contratos
- Endpoint de reprocessamento de contratos
- Logging estruturado com correlation_id
- Validações de regras de negócio
- Idempotência em cancelamentos
"""

API_METADATA = {
    "title": __title__,
    "description": __description__,
    "version": __version__,
    "contact": {
        "name": "Daniel Santos",
        "email": "santos.danielfd@gmail.com",
    },
    "license_info": {
        "name": "MIT",
    },
    "openapi_tags": [
        {
            "name": "contracts",
            "description": "Operações relacionadas a contratos",
        },
        {
            "name": "health",
            "description": "Endpoints de health check",
        },
    ]
}
