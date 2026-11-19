# Fontes oficiais e relatório de validação — Radar Legislativo de Guaramirim

Data da coleta e validação: **19/11/2026**. Período coberto: **01/01/2025 a 19/11/2026** (legislatura 2025–2028).

## 1. Fontes oficiais

| Dado | Onde a Câmara publica | Acesso automático |
|---|---|---|
| Vereadores em exercício (nome, partido, e-mail do gabinete, foto) | https://www.guaramirim.sc.leg.br/camara/membros/exercicio/0 e fichas `/camara/membros/show/<id>` | página com verificação anti-robô |
| Contagem oficial de matérias por vereador e ano | ficha do vereador, `/camara/membros/show/<id>/0/<ano>` (bloco "Atividades Legislativas") | idem |
| Matérias (indicações, moções, pedidos de informação, requerimentos, projetos, vetos) | https://www.guaramirim.sc.leg.br/tramitacoes e `/proposicoes/<tipo>/<ano>/1/<id>` | idem |
| Atas plenárias com ordem do dia e votações (nominais a partir de 30/04/2026) | https://www.guaramirim.sc.leg.br/atas/plenaria | idem |
| Lista de presença de cada sessão | PDF da ata (anexo), em www.cloudsoftcam.com.br/SC/GUARAMIRIM/upload/… | **aberto** (sem verificação) |
| API de dados abertos (vereadores, proposições por tipo e por bairro, pautas) | https://www.guaramirim.sc.leg.br/dadosabertos → `/jsonweb/web-aplicativo.php?keysoft=TOKEN&call=…` | **aberto com token** (cadastro gratuito) |
| Portal da Transparência (despesas, pessoal) — não tem dados legislativos | https://camaraguaramirim.atende.net/transparencia/mapa-do-site | aberto |

O Portal da Transparência (atende.net) **não** publica presenças, proposições nem votações; esses registros estão no portal legislativo (Softcam).

## 2. O que foi coletado

| Item | Quantidade | Observação |
|---|---|---|
| Matérias de 2025–2026 | 888 | 726 indicações, 29 moções, 26 pedidos de informação, 20 requerimentos, 75 projetos/emendas/vetos de vereadores e do Executivo |
| Atas plenárias | 126 | 121 ordinárias, 1 extraordinária, 3 solenes, 1 reunião de composição das comissões |
| Atas com lista de presença lida | 125 | 1 ata (eleição das comissões, 03/02/2025) é PDF escaneado sem texto → **dado indisponível** |
| Votações registradas | 480 | 122 com voto nominal (a partir de 30/04/2026); 358 só com resultado geral |

## 3. Conferência com outra fonte oficial

**Contagens por vereador × ano × tipo** comparadas com a ficha oficial de cada vereador (`/camara/membros/show/<id>/0/<ano>`):
**90 de 90 contagens iguais** (9 vereadores × 2 anos × 5 tipos: indicações, moções, pedidos de informação, requerimentos, projetos). Detalhe em `docs/conferencia-fichas.json`.

Na primeira rodada, 17 contagens de **projetos** divergiam: a listagem geral de matérias não mostra a maioria dos projetos de lei. A divergência foi resolvida incluindo as listas de projetos de cada ficha oficial.

## 4. Conferência manual com os documentos (amostra)

| Vereador | Conferido | Resultado |
|---|---|---|
| Ademir Hubert | Ata nº 055/2026 (10/11/2026), PDF: presença e voto no PL 108/2026 | Bate: presente; voto favorável |
| Jaime Decker | Ata nº 004/2026 (19/02/2026), PDF | Bate: nome não consta na lista de presença (8 presentes) |
| Marcelo Amadeu Deretti | Atas nº 005/2025 (18/02/2025) e 006/2025 (21/02/2025), PDFs | Bate: nome não consta nas duas listas |
| Professora Maria Rosana | Ata nº 019/2025 (24/04/2025), PDF; matéria Indicação 306/2026 | Bate: não consta na lista; autoria da indicação confirmada |
| Marcelo Amadeu Deretti | Indicação 325/2026 (página oficial) | Bate: data 19/11/2026, autoria, ementa |

## 5. Divergências, lacunas e cuidados

- **Ata escaneada:** 1 PDF sem texto (eleição das comissões técnicas, 03/02/2025) — presença marcada como dado indisponível.
- **Votos nominais só a partir de 30/04/2026.** Antes, as atas trazem só o resultado (aprovado/rejeitado). O site mostra apenas o resultado nesses casos.
- **Presidente da sessão** (Emerson Flores da Silva) não vota nas votações comuns; por isso aparece com 0 votos nominais. O site explica isso.
- **"Ausentes" na votação:** a ata registra quem estava ausente na hora da votação; o site mostra separado de "voto dado".
- **Projetos do Poder Executivo:** muitos não aparecem na listagem pública de matérias (ex.: PL 113/2026). Eles aparecem na seção Votações quando votados. As lacunas de numeração por tipo estão listadas no site (Como funciona → O que ainda falta).
- **Indicação 2025:** 1 número da sequência não aparece na listagem pública (pode ter sido retirada/cancelada).
- **Autoria por bancada:** algumas atas citam "Bancada do PSD/MDB/PL"; o Radar usa a autoria nominal da página oficial da matéria.
- **Contato:** só e-mail institucional do gabinete e telefone da Câmara. Um celular publicado na ficha de um vereador **não** foi usado.
- **Licenças/faltas justificadas** não são registradas de forma estruturada; o site diz "não consta na lista", nunca "faltou".

## 6. Coleta automática

O portal legislativo tem verificação anti-robô (reCAPTCHA) nas páginas HTML; o projeto **não** contorna essa proteção. A coleta diária usa:
1. **API de dados abertos** (precisa do token pessoal no segredo `CAMARA_TOKEN`);
2. **PDFs das atas** (servidor aberto).

O instantâneo inicial foi lido por navegador, devagar (1 página a cada 2–3 s), como visitante comum.
**Até o token ser cadastrado, o robô diário roda e valida, mas não traz matérias novas** — o site fica com a última versão validada (19/11/2026). Ao receber o token, é preciso ajustar o `processar.py` ao formato real das respostas da API (salvas em `dados/brutos/api/`).
