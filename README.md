# Radar Legislativo de Guaramirim–SC

Site público do **Adriano Machado Advocacia (OAB/SC 30675)** para os moradores acompanharem a atuação dos vereadores de Guaramirim com **dados oficiais da Câmara Municipal**: presenças, propostas e votos nominais, com link para o documento de origem em cada número.

Método adaptado do guia “Como criar o Radar da sua cidade” (Radar PTlândia, Hortolândia-SP).

Desenvolvido por Juan Campos.

## Estrutura

```
site/                  site estático (GitHub Pages)
  index.html
  assets/              estilo.css, app.js, logo oficial
  dados/radar.json     dados publicados (gerado)
scripts/
  parse_portal.py      leitura do HTML do portal e do texto das atas
  classificar.py       regra única de classificação + extração de ruas/bairros
  pdf_atas.py          baixa os PDFs das atas e lê a lista de presença
  coletar_api.py       coleta pela API de dados abertos (precisa de CAMARA_TOKEN)
  processar.py         junta tudo e gera site/dados/radar.json
  validar.py           checagens antes de publicar
  atualizar.py         orquestra: coleta → processa → valida → publica ou mantém a última versão
config/vereadores.json composição e grafias dos nomes
dados/brutos/          dados oficiais brutos (instantâneos)
dados/historico-coleta.jsonl  registro de cada coleta (aprovada ou reprovada)
docs/                  fontes oficiais e relatório de validação
```

## Rodar localmente

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/pdf_atas.py
.venv/bin/python scripts/processar.py
.venv/bin/python scripts/validar.py site/dados/radar.json
cd site && python3 -m http.server 8080   # abrir http://localhost:8080
```

## Publicação (GitHub Pages + Actions)

1. Repositório público no GitHub com este conteúdo.
2. **Settings → Pages → Source: GitHub Actions.**
3. **Settings → Secrets and variables → Actions → New repository secret**: `CAMARA_TOKEN` = token da API de dados abertos (obtido com cadastro em https://www.guaramirim.sc.leg.br/cidadao e exibido em /dadosabertos).
4. O fluxo `.github/workflows/atualizar.yml` roda todo dia às 04h (Brasília): coleta, valida e publica. Se a coleta falhar ou vier incompleta, **o site continua com a última versão validada** e o erro fica em `dados/historico-coleta.jsonl` + aviso no Actions.

## Por que parte da coleta é um “instantâneo”

As páginas HTML do portal (guaramirim.sc.leg.br) têm uma verificação anti-robô (reCAPTCHA). O projeto **não tenta burlar** essa proteção. O caminho oficial para coleta automática é a **API de dados abertos** da própria Câmara (com token) e os **PDFs das atas**, que ficam em servidor aberto. O instantâneo inicial (2025-01-01 → data da coleta) foi lido devagar, por navegador, como um visitante comum.
