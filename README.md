# VenturaData

![Status](https://img.shields.io/badge/status-incubation-orange)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/github/license/venturalabs-ai/ventura-data)

**Pipeline experimental de engenharia de dados reproduzível com camadas Bronze → Silver → Gold, quality gates e API de consulta.**

> Ecossistema Ventura · [Ventura Studio](https://github.com/venturalabs-ai/ventura-studio)

## Maturidade

**Incubation / experimental.** Existe agora um vertical slice executável, mas o projeto ainda não deve ser apresentado como plataforma de dados pronta para produção.

## Pipeline executável

```text
CSV source
  ↓ validação de contrato
Bronze Parquet
  ↓ tipagem + normalização + quality gate
Silver Parquet
  ↓ agregação analítica
Gold Parquet
  ↓
DuckDB query / FastAPI
```

O contrato de entrada está em `contracts/events.schema.json`. O pipeline bloqueia schema incorreto, dataset vazio, IDs duplicados e valores não numéricos, além de exigir preservação de contagem entre source e Silver.

## Executar

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -e ".[dev]"
ventura-data data/sample/events.csv --warehouse warehouse
```

Consultar o Gold:

```bash
uvicorn ventura_data.api:app --reload
```

Endpoints:
- `GET /health`
- `GET /metrics/categories`

## Evidência automatizada

O CI executa:
- Ruff;
- pytest + branch coverage com gate de 70%;
- pipeline completo sobre dataset versionado;
- validação determinística do Gold;
- upload do warehouse demonstrativo como artefato.

O baseline compartilhado do ecossistema cobre higiene, Trivy HIGH/CRITICAL, SARIF e SBOM; ele não substitui estes testes funcionais específicos do projeto.

## Próximos P1/P2

- OpenLineage;
- orquestração versionada;
- observabilidade e data SLOs;
- fontes públicas reais com snapshots/proveniência;
- incremental loads e idempotência;
- contratos entre produtor e consumidor.

## Licença

Consulte [LICENSE](LICENSE).
