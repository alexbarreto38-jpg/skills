# Gateways de pagamento e operação de pagamentos no Brasil para uma loja/marketplace de bens digitais de games (estilo GGMax)

> **Nota metodológica (ler antes de usar):** pesquisa feita em 12/10/2026. Nesta sessão, a ferramenta de leitura de páginas (WebFetch) não conseguiu acessar nenhum domínio (erro de DNS `ENOTFOUND` em mercadopago.com.br, asaas.com, sejaefi.com.br, stripe.com, woovi.com, transfeera.com, bcb.gov.br), e a cota de buscas da sessão (compartilhada entre agentes) esgotou depois de cerca de 20 buscas. Por isso, **todos os fatos abaixo vêm de trechos e resumos de resultados de busca, sem leitura integral das páginas**. As URLs citadas são as páginas de onde os trechos vieram. Quando o resumo da busca não deixava claro qual URL sustenta o número, eu sinalizo a atribuição como incerta. Vários temas pedidos (chargeback, 3-D Secure, cripto, Pix Automático, Woovi, iugu, Cielo e Adyen) **não puderam ser pesquisados** e estão listados nas seções "Gaps", às vezes com conhecimento prévio marcado como **não verificado**. Tarifas mudam com frequência: a data de cada fonte vai junto dela, quando conhecida.

## 1. Quais provedores são realistas para o negócio, e o que dizem seus termos sobre contas de jogos, itens virtuais e gift cards (incluindo relatos de contas congeladas)?

### Takeaway
Nenhum provedor brasileiro consultado mostrou, nos trechos obtidos, uma proibição explícita a "contas de jogos", mas a página de práticas proibidas do Mercado Pago não pôde ser lida. A Stripe classifica moeda e itens de jogo e gift cards/valor armazenado como **negócios restritos**. O principal risco jurídico e operacional vem de outra frente: os termos das próprias publishers (Riot, Garena/Free Fire, Steam) **proíbem a venda de contas**. Isso aumenta o risco de disputas, de banimento da conta vendida e, por consequência, de reembolsos e chargebacks. Os relatos de bloqueio e retenção de saldo no Mercado Pago são frequentes em geral, mas não encontrei relatos específicos de vendedores de contas de games.

### Cited Findings
**Termos dos provedores**
- **Stripe:** a página oficial "Prohibited and Restricted Businesses" coloca a venda de moeda ou itens de jogo como **restrita**, a menos que o vendedor seja o operador do mundo virtual. Cartões pré-pagos, gift cards e créditos virtuais que armazenam valor monetário também são restritos, e valor armazenado ou créditos mantidos pelo vendedor podem sofrer limites (página sem data, consultada via busca em out/2026) — [Stripe – Prohibited and Restricted Businesses](https://stripe.com/legal/restricted-businesses)
- **Stripe:** o blog oficial justifica as restrições citando stored value e gift cards entre os negócios que atraem lavagem de dinheiro e fraude, e diz que as instituições financeiras precisam monitorar o uso ativamente — [Stripe Blog – Why some businesses aren't allowed](https://stripe.com/blog/why-some-businesses-arent-allowed)
- **Stripe:** um guia de terceiros (2026) alerta que a Stripe atualiza a lista de restritos periodicamente, nem sempre avisando os comerciantes que já são clientes. Fonte secundária — [DirectPayNet – Stripe Restricted & Prohibited Businesses 2026](https://directpaynet.com/business-restricted-from-using-stripe/)
- **Asaas:** a central de ajuda tem um artigo sobre "atividades econômicas de uso restrito". Elas podem ser intermediadas de forma restrita (para um segmento específico, por exemplo) ou mediante documentação complementar. O trecho obtido lista compra e venda de milhas (só PJ), venda de imóveis e veículos, corretagem imobiliária, venda de armas (PJ registrada no Exército) e leilões (só leiloeiros oficiais). **Jogos, contas e itens virtuais não aparecem no trecho**, mas ele estava truncado — [Asaas – Atividades de uso restrito](https://central.ajuda.asaas.com/hc/pt-br/articles/31406442119067-Por-quais-atividades-posso-cobrar-utilizando-o-Asaas)
- **Mercado Pago:** existe uma página oficial "Práticas proibidas para vender", mas só a introdução foi recuperada. **Não foi possível confirmar se ela cita contas ou itens de jogos** — [Mercado Pago – Práticas proibidas para vender](https://www.mercadopago.com.br/ajuda/contornar_estrutura_programas_4822)

**Termos das publishers (risco do produto vendido)**
- A Riot Games diz, nos termos brasileiros, que o conteúdo virtual (moeda do jogo, campeões, skins etc.) é licenciado ao jogador, e não vendido, e que a moeda só pode ser usada no jogo para o qual foi comprada — [Riot Games – Termos de Serviço BR](https://www.riotgames.com/pt-br/terms-of-service-BR)
- A venda de contas de Free Fire é "uma prática comum, mas proibida", porque o jogo não tem sistema oficial de troca (abr/2026) — [TechTudo, abr/2026](https://www.techtudo.com.br/guia/2026/04/comprar-ou-vender-conta-no-free-fire-da-ban-entenda-os-riscos-edjogos.ghtml)
- Um artigo jurídico lista "compartilhamento, venda ou troca de contas" entre as causas comuns de banimento e diz que muitas plataformas proíbem isso expressamente — [Âmbito Jurídico – Banimento de contas de gamers](https://ambitojuridico.com.br/banimento-de-contas-de-gamers-uma-visao-juridica-detalhada/)
- Discussão jurídica sobre compra e venda de contas na Steam — [JusBrasil](https://www.jusbrasil.com.br/artigos/e-proibido-comprar-e-vender-conta-na-steam-saiba-tudo-sobre-a-compra-e-venda-de-contas-na-steam/1876620987)

**Relatos de contas bloqueadas e saldo retido**
- Há reclamações no Reclame Aqui de contas Mercado Pago bloqueadas com dinheiro retido e sem informação — [Reclame Aqui – MP 1](https://www.reclameaqui.com.br/mercado-pago/conta-bloqueada-com-dinheiro-retido-sem-informacao_z1z6qi1P_JRT85Yz/); [Reclame Aqui – MP 2](https://www.reclameaqui.com.br/mercado-pago/conta-bloqueada-valores-retidos-e-falta-de-solucao-do-mercado-pago_CXZTYfuX-vpwEfAw/)
- Em resposta no Reclame Aqui, o Mercado Pago cita seus Termos e Condições, que permitem suspender a conta temporária ou definitivamente, e indica **60 dias** para retirada do saldo após a suspensão (relato individual) — [Reclame Aqui – MP](https://www.reclameaqui.com.br/mercado-pago/conta-bloqueada-valores-retidos-e-falta-de-solucao-do-mercado-pago_CXZTYfuX-vpwEfAw/)
- Um escritório de advocacia fala em bloqueio de saldo de **até 90 dias** após suspensão no Mercado Livre/Mercado Pago, prazo que serviria para cobrir reclamações e chargebacks. Fonte com viés comercial — [Salviatti](https://salviatti.com.br/inteligencia/mercado-livre-conta-bloqueada-saldo-retido); [Mercado Advogados](https://www.mercadoadvogados.com.br/conteudo/saldo-retido-mercado-pago-mercado-livre)
- Advogados distinguem a "reserva temporária para análise de risco", legítima por prazo razoável, da retenção indefinida, sem amparo legal, e citam o art. 884 do Código Civil e o CDC. É opinião de escritório, não jurisprudência consolidada — [Rosenbaum Advocacia](https://www.rosenbaum.adv.br/mercado-pago-bloqueou-conta-saldo-retido-direitos/)
- **AbacatePay:** um usuário relatou que a aprovação da conta levou meses, e o fundador respondeu que o fluxo foi corrigido e hoje aprova em menos de um dia útil (posts de comunidade) — [TabNews – AbacatePay](https://www.tabnews.com.br/Oletros/0efa9c5e-5de5-4bf9-9595-7ed496ad2bbd)

### Inferences
- **Stripe Brasil não é adequada para o core do negócio** (contas e itens de jogos, gift cards de terceiros), porque essas categorias são restritas e dependem de aprovação. O risco é a conta ser encerrada depois de já ter volume. Pode servir em nicho, por exemplo para clientes estrangeiros pagando produtos menos sensíveis, desde que o modelo seja declarado no onboarding.
- Os gateways brasileiros centrados em Pix (Asaas, Efí, Woovi/OpenPix, AbacatePay, Mercado Pago) parecem mais tolerantes, mas a análise de risco é feita **por CNAE e descrição da atividade no cadastro**. A recomendação prática é declarar com transparência "intermediação/venda de bens digitais de games" e pedir por escrito a confirmação de que a atividade é aceita antes de integrar.
- Como a venda de contas viola os ToS das publishers, o catálogo tem perfis de risco diferentes. Gift cards, keys e top-ups comprados de distribuidores autorizados têm risco jurídico menor do que contas, itens e boosting. Uma estratégia de mitigação seria lançar o MVP com mais peso nos produtos de menor risco e tratar contas como categoria de risco elevado, com retenção maior e garantia.
- Ter **pelo menos dois PSPs** em produção (um principal para Pix e um para cartão, ou um de backup) reduz o impacto de um congelamento, que os relatos mostram poder durar de 60 a 90 dias.

### Gaps
- Não consegui ler os termos completos de Mercado Pago, PagBank/PagSeguro, Efí, Pagar.me, iugu, Woovi, Cielo, Adyen e AbacatePay para "contas de jogos/itens virtuais/gift cards". As páginas estavam inacessíveis e a cota de busca esgotou. **Ação sugerida:** ler as listas de atividades proibidas de cada um e confirmar com o comercial.
- Não encontrei relatos específicos (Reddit, Twitter/X, Reclame Aqui) de vendedores de contas de jogos com conta congelada em algum PSP brasileiro. A busca genérica só trouxe bloqueios do Mercado Pago em geral.
- Cielo e Adyen não foram pesquisados. Conhecimento prévio, **não verificado**: ambos costumam exigir volume ou CNPJ estabelecido e análise de risco, e a Adyen tende a atender empresas de grande porte.

## 2. Tarifas atuais (Pix, crédito à vista e parcelado, boleto, débito), prazos de liquidação, antecipação, mensalidades e saques

### Takeaway
No checkout online, o Pix custa de cerca de 0,99% (Mercado Pago) a 1,19%–1,89% (Efí, Pagar.me, PagBank) ou uma tarifa fixa por transação (Asaas R$ 0,99–1,99; AbacatePay cerca de R$ 0,80). O cartão de crédito à vista fica em torno de 3%–5%, e quanto mais rápido o recebimento, mais cara a taxa: no Mercado Pago, 4,98% na hora, 4,49% em 14 dias e 3,98% em 30 dias. Quase todas as fontes encontradas são de terceiros ou estão desatualizadas, e as tabelas oficiais precisam ser confirmadas dentro de cada conta.

### Cited Findings
**Mercado Pago**
- Página oficial do checkout (sem data, consultada via busca em out/2026): crédito **na hora 4,98%**; crédito **14 dias 4,49%**; crédito **30 dias 3,98%**; **Pix na hora 0,99%**; **boleto R$ 3,49** (compensação em até 3 dias); pagamento com saldo Mercado Pago 4,99% na hora; débito virtual Caixa 3,99% na hora — [Mercado Pago – Checkout](https://www.mercadopago.com.br/ferramentas-para-vender/check-out)
- Um artigo de set/2026 traz cartão a 4,99% (na hora ou em 14 dias) e 3,99% em 30 dias — [Mercado Pago Blog – quanto custa vender online](https://www.mercadopago.com.br/blog/quanto-custa-vender-on-line-com-mercado-pago) (atribuição da data incerta; pode ser outra página do conjunto de resultados)
- O recebimento "na hora" pode depender de análise do histórico de vendas e não estar disponível para vendedor novo — [Negócios Financeiros](https://www.negociosfinanceiros.com/taxas-mercado-pago-checkout-transparente-como-funcionam/)
- Novos vendedores podem ter condições de prazo diferentes, e há fonte citando boleto a R$ 3,99 — [ClickGrátis](https://www.clickgratis.com.br/economia/mercado-pago-vender-online-taxas-saldo-recursos/)
- Link de pagamento: Pix a partir de 0,99% e crédito a partir de 3,99% (30 dias), sem custo de criação (agregador, set/2026) — [Calculadora de Taxas – Mercado Pago](https://www.calculadoradetaxas.com.br/public/mercado-pago)

**PagBank/PagSeguro**
- Página oficial: o Pix no checkout de e-commerce ou por QR Code pode ter taxa **limitada a 1,89%**, e o recebimento por chave Pix não tem custo. As taxas podem mudar conforme a negociação comercial — [PagBank – Taxas e tarifas](https://pagbank.com.br/para-seu-negocio/maquininhas/taxas-e-tarifas)
- Guia de terceiro (cerca de jun/2026) para vendas online: débito 1,99%; crédito à vista 4,99% (na hora), 3,99% (14 dias) e 3,19% (30 dias); parcelado 5,59%, 4,59% e 3,79%; boleto R$ 3,99 (2 dias úteis); Pix até 1,89% na hora; **mais R$ 0,40 por transação online** — [Nuvemshop – Como funciona o PagSeguro 2026](https://www.nuvemshop.com.br/blog/como-cobrar-online-com-o-pagseguro/)
- No plano "Na Hora", o valor fica disponível em até 1 hora após a confirmação. Esse blog oficial tem mais de 2 anos e cita débito online a 2,39%, número que conflita com o 1,99% do guia de terceiro — [Blog PagBank – Plano de recebimento](https://blog.pagbank.com.br/plano-de-recebimento-pagbank)

**Asaas**
- Pix: sem taxa de emissão, cobrança só após o pagamento. **R$ 0,99 nos 3 primeiros meses e R$ 1,99 depois**, com isenção nas primeiras 100 transações mensais recebidas por chave ou QR code estático — [Blog Asaas – Pix cobra taxa?](https://blog.asaas.com/pix-cobra-taxa)
- Página oficial: desconto em boleto, cartão e Pix nos 3 primeiros meses para conta nova. As taxas exibidas são padrão, e as condições do contrato aparecem dentro da conta — [Asaas – Pix](https://asaas.com/pix-asaas)
- Um comparativo de 2026 cita cartão a 2,99%, Pix a R$ 0,49 e boleto a R$ 1,99. **A atribuição exata da URL é incerta** (resultado agregado com outros comparativos) — [Kataly – Ranking taxas gateways 2026](https://www.kataly.com.br/blog/ranking-taxas-gateways-pagamento-2026-benchmark)

**Efí (ex-Gerencianet)**
- Site da Efí (2026): **cartão de crédito 3,49%** e **Pix 1,19%**. É material do próprio fornecedor — [Efí – Melhores gateways 2026](https://sejaefi.com.br/blog/melhor-gateway-de-pagamento)
- Emissão de cobranças gratuita, tarifa só no recebimento (infomercial, nov/2023) — [Forbes Brasil, nov/2023](https://forbes.com.br/forbes-money/2023/11/infomercial-efi-bank-oferece-conta-pj-de-alta-performance-para-medios-e-grandes-negocios/)
- Não há planos por faixa de API; tarifa por transação liquidada, negociável por volume (agregador) — [apis.io – Efí pricing](https://apis.io/plans/efi-bank/efi-bank-plans-pricing/)

**Pagar.me (Stone)**
- Página oficial de ofertas, **antiga (cerca de out/2022)**: Pix 0,99%; crédito à vista 4,19%; recebimento no dia seguinte — [Pagar.me – Ofertas](https://www.pagar.me/ofertas)
- Comparativo de 2026 (de um concorrente): Pix **1,19% + R$ 0,99**; crédito à vista **4,39% a 5,59% + R$ 0,99**, conforme o plano; planos empacotados liquidam em cerca de 15 dias — [Chargefy vs Pagar.me (2026)](https://chargefy.io/alternativas/pagarme)
- Comparativo de jul/2026: crédito cerca de 3,19%; boleto R$ 3,49; liquidação de D+2 a D+30 conforme plano e negociação — [Mind Group, jul/2026](https://mindconsulting.com.br/2026/07/gateways-pagamento-online-brasil-comparativo-2026/)
- Antecipação: juros simples sobre o valor líquido, aplicados depois do MDR; o exemplo usa 1% ao mês por parcela (documentação de terceiro, antiga) — [ShopMagento – Pagar.me Antecipação](https://suporte.shopmagento.com.br/knowledgebase.php?article=225)
- As taxas de balcão do parcelado são altas, mas "extremamente negociáveis" para volumes acima de R$ 50 mil/mês (comparativo, 2026) — [Kataly](https://www.kataly.com.br/blog/ranking-taxas-gateways-pagamento-2026-benchmark)

**iugu**
- Os comparativos de 2026 divergem: um traz cartão à vista a 3,34% + R$ 0,40; outro traz cerca de 2,49% + R$ 0,39 e Pix de aproximadamente 0,5%. Atribuição a URL específica incerta — [Kataly](https://www.kataly.com.br/blog/ranking-taxas-gateways-pagamento-2026-benchmark); [Mind Group](https://mindconsulting.com.br/2026/07/gateways-pagamento-online-brasil-comparativo-2026/)

**AbacatePay**
- Pix com tarifa fixa de **cerca de R$ 0,80 por transação**, segundo posts de comunidade, sem página oficial confirmada — [TabNews](https://www.tabnews.com.br/watheusHenry/ef74fc89-2a06-4b3c-b6f5-7fea462e3f11); [GitHub bacen/pix-api – Tarifas Pix cobradas pelos PSPs #266](https://github.com/bacen/pix-api/discussions/266)
- Só aceita Pix. O fundador disse que o cartão estava no roadmap. Um lojista estimou custo efetivo de cerca de 4% no seu ticket médio baixo, porque a tarifa fixa pesa em vendas pequenas — [TabNews](https://www.tabnews.com.br/Oletros/0efa9c5e-5de5-4bf9-9595-7ed496ad2bbd)
- A API cobre cobranças, QR codes Pix, clientes, cupons, saques e webhooks — [API Evangelist – AbacatePay](https://providers.apievangelist.com/providers/abacatepay/)

**Regras gerais de tarifa Pix**
- O BC proíbe cobrar tarifa de pessoas físicas e MEIs pelo uso do Pix, **exceto no recebimento de vendas de produtos e serviços**, que pode ser tarifado. Para PJ, a instituição pode cobrar no envio e no recebimento e define os valores (out/2020) — [O Povo, out/2020](https://www.opovo.com.br/noticias/economia/2020/10/02/pessoas-fisicas-nao-poderao-ser-cobradas-por-uso-do-pix.html)

**Tabela comparativa (valores de balcão; confirmar na conta antes de decidir)**

| Provedor | Pix (checkout) | Crédito à vista | Parcelado | Boleto | Débito | Liquidação do cartão | Fonte/data |
|---|---|---|---|---|---|---|---|
| Mercado Pago | 0,99% (na hora) | 4,98% na hora / 4,49% D+14 / 3,98% D+30 | não obtido | R$ 3,49 (até 3 dias) | 3,99% (débito virtual Caixa) | na hora, 14 ou 30 dias (na hora sujeito a histórico) | [MP Checkout](https://www.mercadopago.com.br/ferramentas-para-vender/check-out), consultado em out/2026 |
| PagBank | até 1,89% | 4,99% na hora / 3,99% 14d / 3,19% 30d, + R$ 0,40 | 5,59% / 4,59% / 3,79% | R$ 3,99 (2 d.u.) | 1,99% (ou 2,39%, conflito) | na hora, 14 ou 30 dias | [PagBank](https://pagbank.com.br/para-seu-negocio/maquininhas/taxas-e-tarifas); [Nuvemshop ~jun/2026](https://www.nuvemshop.com.br/blog/como-cobrar-online-com-o-pagseguro/) |
| Asaas | R$ 0,99 (3 meses) e depois R$ 1,99; 100 grátis/mês em chave ou QR estático | cerca de 2,99% (terceiro) | não obtido | cerca de R$ 1,99 (terceiro) | não obtido | não obtido | [Blog Asaas](https://blog.asaas.com/pix-cobra-taxa); [Kataly 2026](https://www.kataly.com.br/blog/ranking-taxas-gateways-pagamento-2026-benchmark) |
| Efí | 1,19% | 3,49% | não obtido | não obtido | não obtido | não obtido | [Efí 2026](https://sejaefi.com.br/blog/melhor-gateway-de-pagamento) |
| Pagar.me | 1,19% + R$ 0,99 (2026) / 0,99% (2022) | 4,39%–5,59% + R$ 0,99 (2026) / 4,19% (2022) / cerca de 3,19% (jul/2026) | negociável | R$ 3,49 | não obtido | D+2 a D+30; cerca de 15 dias em planos empacotados | [Chargefy 2026](https://chargefy.io/alternativas/pagarme); [Mind Group jul/2026](https://mindconsulting.com.br/2026/07/gateways-pagamento-online-brasil-comparativo-2026/) |
| iugu | cerca de 0,5% (1 fonte) | 3,34% + R$ 0,40 ou cerca de 2,49% + R$ 0,39 (conflito) | não obtido | não obtido | não obtido | não obtido | [Kataly](https://www.kataly.com.br/blog/ranking-taxas-gateways-pagamento-2026-benchmark) |
| AbacatePay | cerca de R$ 0,80 fixo | não oferece | não oferece | não oferece | não oferece | n/a | [TabNews](https://www.tabnews.com.br/watheusHenry/ef74fc89-2a06-4b3c-b6f5-7fea462e3f11) |
| Woovi/OpenPix | **não obtido** | n/a | n/a | n/a | n/a | n/a | — |
| Stripe Brasil | **não obtido** | **não obtido** | — | — | — | — | — |

### Inferences
- Com ticket médio baixo (itens e top-ups de R$ 10–50), a tarifa **percentual** de Pix (0,99%–1,19%) costuma sair mais barata que a fixa (R$ 0,80–1,99). Com ticket alto (contas de R$ 200 ou mais), a tarifa **fixa** vence. A GGMax cobra uma "Taxa Operacional" em compras abaixo de R$ 25 (ver seção 3), o que sugere que a tarifa fixa por transação é um problema real nesse setor.
- No cartão, receber "na hora" custa cerca de 1 ponto percentual a mais que em 30 dias (Mercado Pago e PagBank). Para bens digitais com risco de chargeback, receber em D+30 tem a vantagem adicional de manter um colchão contra estornos, mas prende capital de giro.

### Gaps
- **Woovi/OpenPix:** tarifas não obtidas, porque a busca não trouxe dados e a página oficial estava inacessível. Conhecimento prévio, **não verificado**: Pix a 0,80% com mínimo e máximo por transação.
- **Stripe Brasil:** tarifas de cartão, Pix e boleto não obtidas.
- **Cielo e Adyen:** não pesquisados.
- Faltam tarifas de parcelamento por faixa (2–6x, 7–12x), custo de antecipação atual por provedor, mensalidades e tarifas de saque/TED. Quase nenhuma fonte trouxe esses dados, e eles precisam ser levantados na tabela oficial dentro da conta de cada PSP.

## 3. Quais métodos de pagamento a GGMax e os concorrentes oferecem, e quais provedores parecem usar?

### Takeaway
A GGMax anuncia "mais de 12 formas de pagamento", entre elas cartão de crédito, Pix, boleto, cripto, Saldo GGMAX e GG Points (moeda de fidelidade). Repassa taxas extras em boleto e cripto e cobra uma taxa operacional em compras abaixo de R$ 25. Ela opera com saldo interno e saque apenas para conta do mesmo CPF verificado. **Não identifiquei qual PSP ou adquirente a GGMax usa.**

### Cited Findings
- A página "Formas de pagamento" lista cartão de crédito, Saldo GGMAX, GG Points, cripto, boleto e Pix, e anuncia "mais de 12 formas de pagamento". A página é antiga (cerca de fev/2023) e pode estar desatualizada — [GGMAX – Formas de pagamento](https://ggmax.com.br/formas-de-pagamento)
- Pelos termos de uso, compras abaixo de **R$ 25,00** pagam uma "Taxa Operacional", e pagamentos em **criptomoeda e boleto** podem ter taxas adicionais, exibidas antes da finalização — [GGMAX – Termos de uso](https://www.ggmax.com.br/termos-de-uso)
- Pelos termos de uso, o saque do saldo só pode ir para conta bancária ou de pagamento do **mesmo CPF verificado** na GGMAX, e a chave Pix precisa estar vinculada a essa conta — [GGMAX – Termos de uso](https://www.ggmax.com.br/termos-de-uso)
- Pela política de reembolso, o estorno depende do método: Pix volta para a conta de origem, e cripto é estornada manualmente por um moderador para a carteira de origem — [GGMAX – Política de reembolso](https://ggmax.com.br/politica-de-reembolso)
- GG Points: cotação de **77 GG Points = R$ 1** — [GGMAX – Programa de recompensa](https://ggmax.com.br/programa-de-recompensa)
- A GGMax anunciou a implementação do Pix em post oficial de 2020 — [GGMAX no X](https://x.com/ggmaxoficial)
- A FAQ oficial existe, mas o conteúdo não foi recuperado — [GGMAX – Perguntas frequentes](https://ggmax.com.br/perguntas-frequentes)
- O concorrente Goomax ("Marketplace de Contas e Serviços Digitais") tem uma página de formas de pagamento, cujo conteúdo não foi recuperado — [Goomax – Formas de pagamento](https://goomax.com.br/formas-de-pagamento)

### Inferences
- O modelo da GGMax (saldo interno, saque só para o mesmo CPF, reembolso pelo método de origem, taxa mínima em compras pequenas) é um conjunto de controles antifraude e anti-lavagem. Vale replicá-lo: restringir o saque ao titular verificado reduz o uso da plataforma para "lavar" Pix de golpe, que é exatamente o que gera MED (ver seção 4).
- Repassar ao comprador o custo de cripto e boleto e cobrar taxa mínima abaixo de R$ 25 indica que o custo fixo por transação é relevante no setor.

### Gaps
- **PSP/adquirente da GGMax:** não identificado. Não houve como inspecionar o checkout (scripts de Mercado Pago, Pagar.me, Stripe etc.) nem ler a página de "tarifas e prazos". **Ação sugerida:** abrir o checkout e verificar o domínio do iframe ou SDK de cartão e o recebedor que aparece no QR Pix (o nome do PSP costuma aparecer no app do banco).
- Taxas cobradas do vendedor e prazo de liberação de saldo na GGMax não foram obtidos (busca bloqueada pela cota).
- Concorrentes (Goomax, Eldorado.gg, DFG e outros) não foram pesquisados em detalhe.

## 4. Pix: Pix dinâmico/QR, Pix Automático, webhooks e MED (regras atuais, mudanças de 2025–2026, impacto no lojista e defesa contra MED abusivo)

### Takeaway
O **MED 2.0** é obrigatório desde **2 de fevereiro de 2026**. Ele rastreia o dinheiro por contas subsequentes (a "árvore de transações") e convive com o modelo anterior até 10/05/2026. Desde **1º de setembro de 2026** (IN BCB 766/2026), o **recebedor** tem **80 dias** (antes 30), contados da devolução, para contestar ou pedir o cancelamento de uma devolução feita via MED. Para o lojista de bens digitais, o MED é o equivalente Pix do chargeback: um pagador pode alegar fraude depois de receber o item.

### Cited Findings
**MED 2.0: cronograma e mecânica**
- Slides do Fórum Pix (BCB, 26/03/2026): uso obrigatório do MED 2.0 em **02/02/2026**, convivência com a versão anterior até **10/05/2026** e produção do novo modelo em **11/05/2026** — [BCB – Fórum Pix, 26/03/2026](https://www.bcb.gov.br/content/estabilidadefinanceira/pix/Forum_Pix_Plenaria/20260326-Forum_Pix.pdf)
- O MED 2.0 passou a ser obrigatório para todas as instituições financeiras e de pagamento que operam Pix a partir de fevereiro de 2026 — [Correio Braziliense, 03/02/2026](https://edicao.correiobraziliense.com.br/correiobraziliense/2026/02/03/1355d6/pdf/A08-ECO-0302-DIG.pdf)
- O novo mecanismo permite rastrear toda a rota do dinheiro, incluindo contas subsequentes que receberam partes do valor (nov/2025) — [O Povo+, 24/11/2025](https://mais.opovo.com.br/jornal/economia/2025/11/24/golpe-no-pix-novo-mecanismo-permite-rastrear-toda-a-rota-do-dinheiro.html)
- Devolução em até 11 dias após a contestação, sem garantia: depende de haver saldo nas contas identificadas (ago/2025) — [Cooperativismo de Crédito, ago/2025](https://cooperativismodecredito.coop.br/2025/08/pix-tera-novas-regras-para-devolucao-em-casos-de-fraude/); [MundoCoop](https://mundocoop.com.br/economia-negocios/pix-tera-novas-regras-para-devolucao-em-casos-de-fraude/)
- Um escritório cita a **Resolução BCB nº 493/2025** como base do "MED 2.0", com rastreamento em cadeia e devolução em até 96 horas após a confirmação da fraude. Fonte de escritório, número da norma **não verificado** no BCB — [João Coelho Advocacia](https://joaocoelho.adv.br/med-pix-2/)
- Artigo do Mercado Pago sobre novas regras do Pix em 2026 para contas jurídicas: MED 2.0, Pix Automático e bloqueio cautelar. Segundo o MP, o autoatendimento do MED passou a ser obrigatório a partir de fev/2026 — [Mercado Pago Blog – Novas regras Pix 2026](https://www.mercadopago.com.br/blog/novas-regras-pix-contas-juridicas)
- **Conflito:** fontes de 2025 dizem que a exigência de canal digital de autoatendimento para contestação nos apps começou em **01/10/2025**, e o Mercado Pago fala em fev/2026 — [Revista Oeste](https://revistaoeste.com/economia/pix-vai-ter-novas-regras-para-devolucao-em-casos-de-fraude/); [Mercado Pago Blog](https://www.mercadopago.com.br/blog/novas-regras-pix-contas-juridicas)
- Uma etapa adicional, prevista para agosto, teria sido adiada para outubro (sem detalhes confirmados) — [Tribuna de Jundiaí](https://tribunadejundiai.com.br/mais/brasil/nova-regra-pix-amplia-prazo-de-contestacao/)

**Prazo do recebedor (mudança de set/2026)**
- Desde **01/09/2026**, o prazo para o recebedor contestar ou pedir o cancelamento de uma devolução via MED passou de **30 para 80 dias**, contados **a partir da data da devolução**, pela **Instrução Normativa BCB nº 766/2026**. O prazo da vítima continua sendo de 80 dias a partir da transação original — [Agência Brasil, set/2026](https://agenciabrasil.ebc.com.br/economia/noticia/2026-09/nova-regra-do-pix-amplia-prazo-para-contestar-golpe); [meutudo, 02/09/2026](https://meutudo.com.br/blog/noticias/2026/09/02/prazo-para-contestacao-de-pix-devolvido-pelo-med-passa-de-30-para-80-dias-entenda); [Band](https://www.band.com.br/economia/banco-central-amplia-prazo-de-contestacao-do-pix-med-para-80-dias)

**Bloqueio cautelar**
- O banco do recebedor pode bloquear cautelarmente os valores por até **72 horas** em caso de suspeita de fraude. Uma fonte cita a Resolução BCB nº 147/2021 como base — [Prensali (Substack)](https://prensali.substack.com/p/o-que-e-o-bloqueio-cautelar-e-o-mecanismo-de-devolucao-especial-para-casos-envolvendo-fraudes-com-o-pix); [João Coelho Advocacia](https://joaocoelho.adv.br/med-pix-2/)
- **Conflito nos prazos de análise do banco recebedor:** Band fala em até 7 dias úteis, Santander em até 11 dias corridos — [Band](https://www.band.com.br/economia/banco-central-amplia-prazo-de-contestacao-do-pix-med-para-80-dias); [Santander – O que é MED Pix](https://www.santander.com.br/blog/o-que-e-med-pix)

**Pix dinâmico e webhooks (dados limitados)**
- No Asaas, as primeiras 100 transações mensais recebidas por **chave ou QR code estático** são isentas, e cobranças Pix (QR dinâmico) pagam tarifa por recebimento — [Blog Asaas](https://blog.asaas.com/pix-cobra-taxa)
- A API da AbacatePay oferece QR codes Pix e **webhooks** — [API Evangelist – AbacatePay](https://providers.apievangelist.com/providers/abacatepay/)
- Na homologação da API Pix da Efí, um desenvolvedor relatou que cobranças acima de R$ 9,99 não recebiam retorno, enquanto valores menores funcionavam. O comportamento é só do ambiente de teste — [Fórum Bubble – Efí Bank](https://forum.bubble.io/t/pix-e-cartao-de-credito-efi-bank-gerencianet/362668)

### Inferences
- **Impacto no lojista:** com o MED 2.0, valores recebidos de um Pix fraudulento podem ser bloqueados e devolvidos mesmo depois de repassados para outras contas, inclusive as subcontas de vendedores numa fase de marketplace. Num marketplace de games, o risco típico é o golpista usar um Pix roubado ou de vítima de golpe para comprar um item, que é entregue na hora, e a vítima acionar o MED depois.
- **Defesa contra MED abusivo** (com base nas regras acima e em boas práticas, sem fonte específica de "defesa"):
  1. Exigir que o **pagador do Pix seja o mesmo titular (CPF) da conta do comprador** na plataforma (o PSP devolve nome e CPF do pagador no webhook) e recusar ou estornar pagamentos de terceiros. Isso imita o controle de saque da GGMax.
  2. Guardar evidências de entrega: logs de acesso, IP, device fingerprint, chat, confirmação do comprador e registro de troca de e-mail/senha da conta.
  3. Usar o **prazo de 80 dias** (desde 01/09/2026) para contestar devoluções indevidas via PSP.
  4. Para produtos de alto valor e risco, **segurar a liberação** ao vendedor (escrow) por um período e limitar valores de primeiras compras.
- Pix é a opção mais barata e não tem chargeback de cartão, mas **não é irrevogável** por causa do MED. Ele precisa de um processo de risco próprio.

### Gaps
- **Pix Automático:** não pesquisado (cota esgotada). Conhecimento prévio, **não verificado**: lançado pelo BC em 16/06/2025 para cobranças recorrentes com autorização única. Tem pouca relevância para venda avulsa e serviria só a assinaturas, como um clube VIP.
- Não obtive o texto do Regulamento do Pix ou do Manual do MED com os prazos oficiais de análise e devolução, nem o número correto da resolução do MED 2.0 (493/2025 é citada só por escritório).
- Não encontrei guias específicos de "defesa do recebedor" em MED abusivo nem estatísticas de MED em e-commerce de bens digitais.
- Detalhes de webhooks (latência, reenvio, assinatura) por PSP não foram obtidos.

## 5. Chargebacks de cartão: funcionamento no Brasil, taxas típicas em bens digitais, liability shift do 3-D Secure, produtos de proteção e evidências para disputas de entrega digital

### Takeaway
**Tema não pesquisado:** a cota de buscas esgotou antes desta seção, e nenhuma fonte foi coletada. A única evidência indireta é que o saldo retido em contas suspensas do Mercado Pago (60–90 dias) é justificado por reclamações, contestações e chargebacks.

### Cited Findings
- O saldo pode ficar retido por reclamações, contestações ou chargebacks, e advogados recomendam guardar e-mails, prints, protocolos e comprovantes de envio — [Salviatti](https://salviatti.com.br/inteligencia/mercado-livre-conta-bloqueada-saldo-retido); [Rosenbaum Advocacia](https://www.rosenbaum.adv.br/mercado-pago-bloqueou-conta-saldo-retido-direitos/)
- O Mercado Pago destaca que seu checkout inclui sistema antifraude — [Adobe Commerce Marketplace – Mercado Pago](https://commercemarketplace.adobe.com/mercadopago-adb-payment.html)

### Inferences
- Como a venda de contas viola os ToS das publishers (seção 1), contas recuperadas pelo vendedor original ou banidas tendem a gerar disputas legítimas ("produto não recebido ou não funciona"). Esse risco é diferente do de fraude com cartão roubado e não é coberto pelo liability shift do 3DS, que só transfere a responsabilidade em disputas por fraude.

### Gaps
Todos os pontos abaixo **precisam de pesquisa**. O conhecimento prévio vai marcado como **não verificado**:
- Taxas típicas de chargeback em bens digitais no Brasil (sem dado).
- Liability shift do 3-D Secure 2.x no Brasil. Conhecimento prévio, não verificado: com autenticação 3DS bem-sucedida, a responsabilidade por chargeback de **fraude** passa ao emissor, mas disputas de "desacordo comercial" continuam com o lojista. Os programas de monitoramento das bandeiras (Visa VAMP, Mastercard ECM/ECP) impõem multas acima de certos limiares.
- Produtos de proteção: "Proteção contra contestações" do Mercado Pago, garantia de chargeback de antifraudes como ClearSale e Konduto, Radar da Stripe. Condições e preços não obtidos.
- Evidências para entrega digital (logs, IP, aceite de termos, confirmação de recebimento) segundo as regras de cada bandeira: não obtidas.

## 6. Fase marketplace: split de pagamentos, retenção de valores (escrow) legal, subcontas, KYC de vendedores e implicações regulatórias (subcredenciador, instituição de pagamento)

### Takeaway
A **Resolução BCB nº 522, de 10/11/2025**, define o subcredenciador e torna **obrigatória sua participação na liquidação centralizada** quando ele atua como recebedor ou pagador dos fluxos. Para um marketplace pequeno, o caminho prudente é **não tocar no dinheiro dos vendedores**: usar o split ou as subcontas de um PSP autorizado (Asaas, Pagar.me, Mercado Pago, Efí, iugu e outros), que cuida do KYC do vendedor e da custódia.

### Cited Findings
- A Resolução BCB 522 (10/11/2025) define o subcredenciador como participante de arranjo que habilita exclusivamente usuários finais recebedores a aceitar instrumentos de pagamento, sem participar da liquidação como credor perante o emissor, e torna obrigatória sua participação na liquidação centralizada quando atua como recebedor ou pagador — [LegisWeb – Resolução BCB nº 522/2025](https://www.legisweb.com.br/legislacao/?id=486238)
- A Circular BCB 3.886/2018 definiu a figura do subcredenciador com critérios objetivos de identificação — [Migalhas](https://www.migalhas.com.br/depeso/277839/banco-central-disciplina-a-figura-do-subcredenciador)
- Desde 2017, operações de marketplaces são liquidadas via CIP, e os recursos vão direto à conta do recebedor final, sem transitar pelo subcredenciador — [Machado Meyer](https://www.machadomeyer.com.br/pt/imprensa-ij/liquidacao-de-operacoes-no-e-commerce-subcredenciadores)
- O Mercado Pago diz que marketplaces com split precisam operar por meio de instituições de pagamento autorizadas ou cumprir as normas vigentes (fonte comercial) — [Mercado Pago Blog – Split de pagamento](https://www.mercadopago.com.br/blog/split-pagamento-complexo-marketplace)
- Análise de mercado sobre por que marketplaces estão se tornando subadquirentes (conteúdo não detalhado nos resultados) — [Malga](https://malga.io/post/regulacao-marketplaces-subadquirente/)
- Panorama sobre a regulamentação do BACEN para marketplaces — [AARB](https://www.aarb.org.br/newsletter/tudo-que-voce-precisa-saber-sobre-a-nova-regulamentacao-do-bacen-para-marketplacespor-ana-capelhuchnik/)
- Uma fonte cita a Circular 3.815/16 como origem da exigência de split, informação não confirmada — [YAV Digital](https://yavdigital.com.br/blog/split-de-pagamento-e-commerce-o-que-e-como-funciona/)
- Visões gerais de split pela Cielo e pela Barte — [Cielo Blog](https://blog.cielo.com.br/vender-online/split-de-pagamento/); [Barte](https://www.barte.com/blog-posts/split-de-pagamento-o-que-e-e-como-funciona)

### Inferences
- **MVP (vendedor único):** o dinheiro é do próprio lojista, então não há questão de subcredenciamento.
- **Fase marketplace:** se a plataforma receber o pagamento na sua conta e depois repassar aos vendedores, pode ser caracterizada como subcredenciador ou instituição de pagamento. Isso traz obrigações de liquidação centralizada (Res. BCB 522/2025) e possivelmente de autorização. O desenho mais seguro é cada vendedor ter **subconta no PSP**, com **split na origem** (a comissão da plataforma vai para a conta dela e o restante para a subconta do vendedor). Assim, o **KYC** e a custódia ficam com o PSP regulado.
- **Escrow:** em vez de a plataforma guardar o dinheiro, use o mecanismo de **retenção/liberação programada** do PSP no split (liberar ao vendedor após a confirmação de entrega ou depois de X dias). A GGMax limita o saque ao CPF verificado (seção 3), um controle a replicar.
- O MED 2.0 rastreia contas subsequentes (seção 4), então subcontas de vendedores que receberem dinheiro de fraude podem ser bloqueadas. Uma retenção mínima antes da liberação reduz o prejuízo para a plataforma.

### Gaps
- Não confirmei o limite de volume que obriga um marketplace ou subcredenciador a pedir autorização ao BC como instituição de pagamento. A busca não encontrou o valor, e a "faixa de R$ 500 milhões" da pergunta segue sem confirmação.
- Não obtive a documentação de split e subcontas de cada PSP (Asaas, Pagar.me, Mercado Pago Marketplace, Efí, iugu, Woovi): custos, KYC exigido do vendedor e retenção configurável.
- Não pesquisei obrigações de prevenção à lavagem de dinheiro (Lei 9.613/1998 e COAF) aplicáveis ao marketplace.

## 7. Alternativas: cripto e stablecoins, processadores internacionais para clientes estrangeiros e carteira ou saldo interno (implicações regulatórias)

### Takeaway
A GGMax já aceita cripto (com taxa extra e estorno manual) e opera um **saldo interno** mais uma moeda de fidelidade (GG Points). Isso mostra que esses modelos são usados no setor. As implicações regulatórias (prestadoras de serviços de ativos virtuais, emissão de moeda eletrônica ou conta de pagamento pré-paga) **não foram pesquisadas** porque a cota de buscas esgotou. A Stripe restringe créditos e valor armazenado mantidos pelo vendedor.

### Cited Findings
- A GGMax aceita criptomoeda, com taxa adicional exibida no checkout, e faz o estorno manualmente à carteira de origem — [GGMAX – Termos de uso](https://www.ggmax.com.br/termos-de-uso); [GGMAX – Política de reembolso](https://ggmax.com.br/politica-de-reembolso)
- A GGMax opera Saldo GGMAX, com saque só para conta do mesmo CPF verificado, e GG Points (77 pontos = R$ 1) — [GGMAX – Termos de uso](https://www.ggmax.com.br/termos-de-uso); [GGMAX – Programa de recompensa](https://ggmax.com.br/programa-de-recompensa)
- A Stripe trata como restritos créditos virtuais e valor armazenado mantidos pelo vendedor, que podem sofrer limites — [Stripe – Restricted Businesses](https://stripe.com/legal/restricted-businesses)

### Inferences
- **Saldo interno:** um saldo que só pode ser usado na própria loja (crédito de loja ou cashback não sacável) tende a ter risco regulatório menor que um saldo **sacável e transferível**, que se parece com uma conta de pagamento pré-paga ou moeda eletrônica. Para o MVP, a alternativa mais segura é não ter saldo sacável. Na fase marketplace, o "saldo do vendedor" deveria ser o saldo da subconta no PSP, e não um passivo da plataforma.
- **Clientes estrangeiros:** Stripe e similares restringem o núcleo do catálogo (seção 1), o que limita essa via. Cripto (USDT/USDC) é a alternativa de fato usada pela GGMax.

### Gaps
Pontos que **precisam de pesquisa**; o conhecimento prévio vai marcado como **não verificado**:
- Regras do BC para prestadoras de serviços de ativos virtuais (VASPs). Conhecimento prévio, não verificado: Lei 14.478/2022 (marco legal) e resoluções do BC de nov/2025 (citadas como 519, 520 e 521/2025) com regras de autorização de VASPs e tratamento de stablecoins em pagamentos e câmbio. Não confirmei número, vigência nem impacto para um lojista que só **aceita** cripto por meio de um processador.
- Regulação de saldo e carteira: Lei 12.865/2013 (arranjos e instituições de pagamento, emissor de moeda eletrônica) e limites de dispensa de autorização. Não pesquisado.
- Processadores internacionais (dLocal, PayPal, EBANX, Payoneer, Xsolla e similares) e se aceitam bens digitais de games: não pesquisados.

## 8. Recomendação preliminar: MVP (loja de vendedor único) e fase marketplace

### Takeaway
**MVP:** Pix como meio principal, por um PSP brasileiro com API e webhooks e tarifa baixa (Mercado Pago 0,99%, Efí 1,19%, ou Asaas e AbacatePay com tarifa fixa para tickets maiores). Cartão por um provedor que aceite formalmente o segmento, com antifraude e 3DS, recebendo em D+14/D+30 para manter colchão. Nada de Stripe para o núcleo do catálogo. **Marketplace:** split com subcontas em PSP autorizado, com retenção e liberação programada, para não virar subcredenciador nem custodiante (Res. BCB 522/2025).

### Cited Findings
- Pix: 0,99% no Mercado Pago, 1,19% na Efí, até 1,89% no PagBank, R$ 0,99–1,99 no Asaas e cerca de R$ 0,80 na AbacatePay — [MP Checkout](https://www.mercadopago.com.br/ferramentas-para-vender/check-out); [Efí](https://sejaefi.com.br/blog/melhor-gateway-de-pagamento); [PagBank](https://pagbank.com.br/para-seu-negocio/maquininhas/taxas-e-tarifas); [Blog Asaas](https://blog.asaas.com/pix-cobra-taxa); [TabNews](https://www.tabnews.com.br/watheusHenry/ef74fc89-2a06-4b3c-b6f5-7fea462e3f11)
- Na Stripe, moeda e itens de jogo, gift cards e valor armazenado são restritos — [Stripe](https://stripe.com/legal/restricted-businesses)
- MED 2.0 em vigor desde 02/02/2026, e recebedor com 80 dias para contestar desde 01/09/2026 — [BCB Fórum Pix](https://www.bcb.gov.br/content/estabilidadefinanceira/pix/Forum_Pix_Plenaria/20260326-Forum_Pix.pdf); [Agência Brasil](https://agenciabrasil.ebc.com.br/economia/noticia/2026-09/nova-regra-do-pix-amplia-prazo-para-contestar-golpe)
- Resolução BCB 522/2025 sobre subcredenciadores e liquidação centralizada — [LegisWeb](https://www.legisweb.com.br/legislacao/?id=486238)
- Controles da GGMax: saque só para o mesmo CPF e taxa operacional abaixo de R$ 25 — [GGMAX – Termos](https://www.ggmax.com.br/termos-de-uso)

### Inferences
- **MVP, desenho sugerido:**
  1. **Pix (principal):** QR dinâmico por pedido, confirmação por webhook e entrega automática. Exigir que o CPF do pagador seja igual ao do comprador cadastrado.
  2. **Cartão (secundário):** um PSP que aceite o segmento por escrito (candidatos: Mercado Pago, Pagar.me, Asaas, Efí, PagBank), com 3DS e antifraude ativos e limites de valor para clientes novos.
  3. **Um segundo PSP de contingência** já integrado.
  4. Taxa mínima ou operacional em pedidos pequenos, como faz a GGMax.
- **Escolha entre os PSPs Pix:** se o ticket médio for menor que cerca de R$ 100, a tarifa percentual de 0,99% (Mercado Pago) sai mais barata. Com ticket médio de R$ 150 ou mais, a tarifa fixa (Asaas R$ 1,99, AbacatePay cerca de R$ 0,80) passa a compensar. O ponto de equilíbrio entre 0,99% e R$ 1,99 é cerca de R$ 201. Entre 0,99% e R$ 0,80, é cerca de R$ 81.
- **Fase marketplace:** priorizar PSPs com split nativo e subcontas (Asaas, Pagar.me, Mercado Pago, Efí, iugu, Woovi; capacidades a confirmar), liberação condicionada à confirmação de entrega e KYC do vendedor feito pelo PSP. Consultar um advogado regulatório sobre a Res. BCB 522/2025 e sobre manter "saldo" sacável.
- Validar com cada PSP, **antes de integrar**, a aceitação explícita de "contas de jogos", "itens virtuais", "gift cards" e "boosting". É o principal fator de risco de congelamento.

### Gaps
- A recomendação é preliminar. Ela depende da confirmação dos termos de cada PSP, das tarifas de parcelamento e antecipação e das regras de chargeback e 3DS, que não foram pesquisadas (seções 2, 5 e 7).
