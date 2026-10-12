# Segurança e antifraude em lojas e marketplaces de contas, itens, gift cards e keys de jogos (foco Brasil, out/2026)

> **Nota metodológica (12/out/2026).** Esta pesquisa foi interrompida por duas limitações. O orçamento de buscas compartilhado entre os agentes acabou depois de 10 buscas, e a ferramenta de leitura de páginas (WebFetch) falhou com erro de DNS em todos os domínios testados: bcb.gov.br, ggmax.com.br, intercom.help, mercadopago.com.br, clear.sale, owasp.org e chargebackgurus.com. Por isso:
> (a) os itens em "Cited Findings" sem marcação vêm de resultados de busca que resumiam a página citada. Não li a página inteira, então vale reconferir números antes de publicar.
> (b) os itens marcados **[NV]** (não verificado nesta sessão) vêm do conhecimento prévio do modelo, que vai até jun/2026. Só incluí um link quando a URL canônica é bem conhecida, e ela também não foi aberta nesta sessão. Trate esses itens como "a confirmar".
> (c) as "Inferences" são recomendações de desenho de controles derivadas dos achados. Não são fatos com fonte.

---

## 1. Tipologia de fraudes (contra o comprador e contra a loja), com exemplos reais

### Takeaway
As fraudes que mais se repetem no setor são quatro: a **recuperação da conta pelo dono original depois da venda** ("pullback"), o **comprador que toma a conta de volta ou pede reembolso e continua com ela**, o **chargeback ou fraude amigável no cartão** e o **golpe com intermediário ou site falso**. No Brasil entram também o **Pix**, com o MED 2.0 obrigatório desde fev/2026 e o autoatendimento que facilita contestar, e a alta incidência de fraude em **games e gift cards** registrada pela ClearSale.

### Cited Findings

**Recuperação da conta após a venda (pullback / "recuperar conta vendida")**
- Um guia do Free Fire Mania lista entre os golpes mais comuns no mercado de contas de Free Fire: "receber pagamento e desaparecer, entregar contas falsas, **recuperar a conta após a venda** e utilizar intermediários falsos". — [Free Fire Mania – busca por contas e riscos](https://www.freefiremania.com.br/noticia/conta-free-fire-buscas-riscos-jogadores.html); [Free Fire Mania – comprar conta é seguro?](https://www.freefiremania.com.br/noticia/comprar-conta-free-fire-e-seguro.html)
- Segundo o mesmo veículo, o suporte oficial da Garena normalmente não ajuda quem comprou uma conta, porque ela não está no nome do comprador e a transação viola as regras do jogo. O comprador que sofre pullback fica sem recurso junto à publisher. — [Free Fire Mania – comprar conta é seguro?](https://www.freefiremania.com.br/noticia/comprar-conta-free-fire-e-seguro.html)
- Há também o golpe do "recuperador de conta": o Free Fire Mania avisa que "nenhum site ou pessoa pode recuperar sua conta FF sem o login original", alerta contra quem cobra para "recuperar" contas e orienta usar só o suporte oficial (ffsupport.garena.com). — [Free Fire Mania – recuperar conta (2026)](https://www.freefiremania.com.br/recuperar-conta-free-fire.html)
- A GGMax retém o saldo do vendedor por mais tempo em contas de publishers com maior risco de recuperação. Numa reclamação, uma conta de Clash Royale vendida em 09/07/2026 teve o saldo liberado só em 30/07/2026, quase 30 dias depois, embora a tabela da plataforma prometa 7 dias para "Vendas de contas". O suporte justificou dizendo que contas da Supercell exigem "prazo de segurança" estendido. Segundo o reclamante, essa exceção não aparece nas tabelas públicas. — [Reclame Aqui, jul/2026](https://www.reclameaqui.com.br/ggmax/retencao-abusiva-de-saldo-ggmax-promete-prazo-de-7-dias-e-retem-valor-por-30-dias-apos-venda-de-clash-royale_kCs-xdRIYG2PhgBG/)
- A Eldorado.gg cancela a venda e reembolsa se, dentro da garantia de 5 dias, a conta "parar de funcionar, for banida ou recuperada". Depois desse prazo, a plataforma não garante devolução do dinheiro, mas investiga casos de recuperação e o vendedor continua podendo ser responsabilizado. — [Eldorado Help Center – Account Warranty](https://intercom.help/eldoradogg/en/articles/8408988-account-warranty)
- Avaliações no Trustpilot (fim de 2024 e 2026) relatam vendedores da Eldorado recuperando contas depois da janela de 5 dias e disputas encerradas sem investigação. São relatos individuais, não confirmados. — [Trustpilot Eldorado.gg](https://au.trustpilot.com/review/eldorado.gg?page=4)
- No G2G, compradores relatam reembolso negado depois que a conta foi tomada de volta. Um deles diz que uma conta de Spotify banida logo após a compra não foi reembolsada porque o pedido já estava marcado como "completed". — [Trustpilot G2G](https://www.trustpilot.com/review/www.g2g.com?page=8); [Trustpilot G2G (IE)](https://ie.trustpilot.com/review/www.g2g.com?page=3)
- Um guia sobre a PlayerAuctions avisa que o dono original ainda pode conseguir recuperar uma conta vendida. — [CyberPost](https://cyberpost.co/is-it-safe-to-sell-account-on-playerauctions/)

**Fraude do comprador contra o vendedor (tomar a conta de volta ou receber o reembolso e continuar com ela)**
- Um vendedor reclamou no Trustpilot que um comprador da PlayerAuctions tomou a conta e a esvaziou. A PlayerAuctions respondeu citando seu "after-sale protection process" e os "evidence requirements". É a versão de uma das partes. — [Trustpilot PlayerAuctions](https://au.trustpilot.com/review/playerauctions.com?page=2)
- Em outra disputa, a PlayerAuctions "congelou temporariamente o reembolso do comprador" para que o vendedor pedisse a conta de volta ou a recuperasse diretamente, e disse que isso costuma ser necessário em casos parecidos. — [Trustpilot PlayerAuctions (FI)](https://fi.trustpilot.com/review/playerauctions.com?page=3)
- A Eldorado orienta que, depois do reembolso, o comprador pare de usar a conta, porque a garantia deixa de cobri-la. Isso mostra que a plataforma reconhece o risco de reembolsar e o comprador seguir usando a conta. — [Eldorado Help Center – TradeShield](https://intercom.help/eldoradogg/en/articles/8409006)

**Chargeback e fraude amigável (first-party misuse) no cartão**
- O Visa Compelling Evidence 3.0 (CE 3.0) é a regra de evidência para contestar disputas de fraude em compras sem cartão presente (reason code 10.4) em que o próprio titular parece ter comprado. Vale desde **15/04/2023**. O comerciante precisa mostrar transações anteriores não contestadas do mesmo titular, de 120 a 365 dias antes, que compartilhem pelo menos dois identificadores (IP, device ID, conta/login etc.). **As fontes divergem** sobre os limites exatos, e uma delas fala em 3 elementos coincidentes. — [Chargebacks911/Chargeback Gurus](https://www.chargebackgurus.com/blog/visa-compelling-evidence-3.0); [Nomupay](https://nomupay.com/compelling-evidence-3-0-your-new-chargeback-defence); [TaskUs](https://www.taskus.com/insights/how-visa-ce-3-0-helps-stop-friendly-fraud-protects-margins/); [Paytia](https://www.paytia.com/glossary/compelling-evidence)
- Pela regra anterior, para bens digitais, dois ou mais entre IP, device ID e e-mail precisavam coincidir. — [Chargeback Gurus](https://www.chargebackgurus.com/blog/visa-compelling-evidence-3.0); [Nomupay](https://nomupay.com/compelling-evidence-3-0-your-new-chargeback-defence)
- O CE 3.0 só reduz a perda com fraude amigável se o comerciante já estiver guardando o histórico de dados das transações (IP, dispositivo, login) **antes** da disputa. — [Nomupay](https://nomupay.com/compelling-evidence-3-0-your-new-chargeback-defence)
- Um avaliador da Eldorado relata em 2026 que teve a conta banida depois de abrir disputa no banco. Isso indica que os marketplaces banem quem faz chargeback (relato individual). — [Trustpilot Eldorado.gg](https://au.trustpilot.com/review/eldorado.gg?page=4)

**Cartões roubados e tentativas de fraude em games e gift cards (Brasil)**
- Num estudo da ClearSale de jan/2025, **games** ficaram em 1º lugar entre as categorias com mais tentativas de fraude no início do ano (5,4%), pelo 2º ano seguido. A atribuição à ClearSale vem do resumo da busca. — [Monitor Mercantil](https://monitormercantil.com.br/janeiro-registrou-mais-de-r-200-milhoes-em-tentativas-de-fraude-no-e-commerce/)
- O Mapa da Fraude 2025 da ClearSale (com dados de 2024) aponta **gift cards** com alta incidência de fraude em datas comerciais: 12,2% no Dia do Consumidor e 12,4% no Dia dos Pais. Na Black Friday, um **gift card digital Airbnb de R$ 500** aparece entre os produtos mais visados. — [ClearSale – Mapa da Fraude 2025 (PDF)](https://en.clear.sale/hubfs/MapaDaFraude2025_Report.pdf); [ClearSale – Mapa da Fraude](https://br.clear.sale/en/mapa-da-fraude)
- Não achei edição 2026 do Mapa da Fraude da ClearSale com recorte de games. A Serasa Experian publicou um "Mapa da Fraude" do 1º trimestre de 2026, mas sem recorte de games ou gift cards nos trechos encontrados. — [Serasa Experian – Antifraude](https://www.serasaexperian.com.br/solucoes/antifraude/)
- Série histórica da Konduto ("Raio-X da Fraude", **dados antigos**): taxa de tentativas de fraude no e-commerce brasileiro de 3,03% (2017), 2,20% (2018), 2,52% (2019) e 3,49% no 1º semestre de 2020, com pico de 3,99% em mar/2020. Os relatórios lembram que "tentativa" não é fraude efetiva. — [Correio Braziliense (2018)](https://blogs.correiobraziliense.com.br/servidor/indice-de-tentativas-de-fraude-no-e-commerce-brasileiro-caiu-273-em-2018/); [Consumidor Moderno (2019)](https://www.consumidormoderno.com.br/2020/03/13/tentativas-de-fraude-crescem-em-2019/); [Mercado & Consumo (1S2020)](https://mercadoeconsumo.com.br/21/10/2020/varejo-digital/tentativas-de-fraude-no-e-commerce-ficou-em-349-no-primeiro-semestre-de-2020-segundo-estudo-da-konduto/)

**Pix: MED, bloqueio cautelar e abuso do mecanismo de devolução**
- O **MED 2.0** passou a ser obrigatório em **02/02/2026**, conforme a **Resolução BCB nº 493/2025**. A resolução também criou a função "Recuperação de Valores" e o grupo de segurança GE-Seg, e deixou prazos e fluxos operacionais para o manual do DICT. — [Mercado Pago – Novas regras do Pix 2026](https://www.mercadopago.com.br/blog/novas-regras-pix-contas-juridicas); [Finsiders Brasil](https://finsidersbrasil.com.br/?p=345777)
- O **autoatendimento do MED** é 100% digital desde **01/10/2025**: todos os bancos participantes devem oferecer a contestação dentro da área Pix do app, sem falar com o atendimento. — [O Imparcial, ago/2025](https://oimparcial.com.br/noticias/2025/08/banco-central-moderniza-pix-e-med-permitira-devolucao-de-recursos-de-forma-totalmente-digital/)
- Uma fonte diz que o autoatendimento cobre transações dos **80 dias anteriores**, citando o InfoMoney. **Não confirmei isso no texto da norma.** — [Okai](https://okai.com.br/artigo/med-20-como-a-nova-resolucao-reforca-a-seguranca-do-pix)
- O MED 2.0 faz **bloqueio em cadeia** de até **cinco camadas** de contas seguintes, e os recursos ficam bloqueados automaticamente quando a notificação é registrada no DICT. O BC fala em devolução em **até 11 dias** após a contestação. — [O Povo, nov/2025](https://mais.opovo.com.br/jornal/economia/2025/11/24/golpe-no-pix-novo-mecanismo-permite-rastrear-toda-a-rota-do-dinheiro.html); [Okai](https://okai.com.br/artigo/med-20-como-a-nova-resolucao-reforca-a-seguranca-do-pix)
- O MED 2.0 passa a monitorar **contas empresariais** com os mesmos critérios das contas de pessoa física. — [Mercado Pago](https://www.mercadopago.com.br/blog/novas-regras-pix-contas-juridicas)
- O **bloqueio cautelar** de Pix sob suspeita de fraude dura no máximo **72 horas** (Res. BCB 1/2020, art. 39-B, §4º, segundo uma decisão judicial) e não autoriza deixar a conta indisponível por tempo indeterminado. Contratos de conta PJ, como o do BRB em 2026, já trazem essa cláusula. — [Vade Mecum – jurisprudência](https://www.vademecumprevidenciario.com.br/jurisprudencia/eme/483.0755.0649.2899); [BRB – contrato de conta PJ (abr/2026)](https://novo.brb.com.br/wp-content/uploads/2026/04/ABERTURA-DE-CONTAS-DE-DEPOSITO-PJ_1o-Oficio_00995453.pdf); [Âmbito Jurídico](https://ambitojuridico.com.br/?p=9055304)

**Phishing, sites clonados e falso intermediário**
- "Intermediários falsos" estão entre os golpes mais comuns na venda de contas de Free Fire. — [Free Fire Mania](https://www.freefiremania.com.br/noticia/conta-free-fire-buscas-riscos-jogadores.html)
- Há vários domínios com "ggmax" no nome e reputações diferentes nos verificadores. Um deles, ggmaxpro.life, é recente. Esses agregadores não dão veredito técnico, mas os domínios parecidos existem e servem de vetor de clone. — [Site Confiável – ggmaxpro.life](https://www.siteconfiavel.com.br/site/ggmaxpro-life); [Site Confiável – ggmax.com.br](https://www.siteconfiavel.com.br/site/ggmax-com-br); [Site Confiável – ggmax.com](https://www.siteconfiavel.com.br/site/ggmax-com)
- Golpistas copiam o design de sites confiáveis e hospedam as páginas em serviços legítimos como o Google Sites (2022). Em 2025 apareceu uma técnica de phishing que usa domínio do Google. — [Olhar Digital, nov/2022](https://olhardigital.com.br/2022/11/02/seguranca/google-sites-e-alvo-de-golpistas-entenda-como-se-proteger/); [Olhar Digital, abr/2025](https://olhardigital.com.br/2025/04/23/seguranca/nova-tecnica-de-phishing-usa-dominio-do-google-para-aplicar-golpe/)
- Recomendações aos compradores: nunca compartilhar códigos de verificação, desconfiar de preço muito baixo e pedir **vídeo** mostrando o login e o inventário, porque prints podem ser manipulados. — [JivoChat](https://www.jivochat.com.br/blog/reviews/servicos/comprar-conta-de-free-fire-e-possivel.html)

#### [NV] Conhecimento prévio relevante, a confirmar antes de publicar
- **[NV]** A Lei 14.155/2021 incluiu a "fraude eletrônica" no art. 171 do Código Penal (§2º-A), com pena maior. É a base para boletins de ocorrência contra golpistas. — [Planalto – Lei 14.155/2021](https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14155.htm)
- **[NV]** Os termos de uso das principais publishers (Steam SSA, Riot, Epic, Roblox, Supercell, Garena) proíbem vender ou transferir contas. A publisher pode banir a conta, o que vira risco de "conta banida após venda" e reduz a ajuda do suporte ao comprador. — [Steam Subscriber Agreement](https://store.steampowered.com/subscriber_agreement/)

### Inferences
**Tipologia consolidada (o que é, quem perde e o principal sinal).** É síntese a partir dos achados acima e do conhecimento do setor:

| # | Fraude | Vítima principal | Como acontece | Sinais e controles principais |
|---|---|---|---|---|
| 1 | **Pullback** (dono original recupera a conta) | Comprador e, numa loja que vende sozinha, **a loja**, que comprou a conta de um fornecedor | O fornecedor ou dono original prova a posse ao suporte da publisher (recibos de compra, e-mail de criação, dados de pagamento) | Só comprar contas com e-mail original e recibos; carência antes de revender; pagar o fornecedor só depois da carência; KYC do fornecedor |
| 2 | **Conta roubada ou hackeada revendida** | Vítima original, comprador final e loja (perde a conta e a reputação) | Contas obtidas por phishing, stealer ou credential stuffing chegam ao estoque | KYC e histórico do fornecedor; recusar contas sem e-mail original; checar se o e-mail aparece em vazamentos; consultar listas de contas denunciadas |
| 3 | **Chargeback / fraude amigável** | Loja | O comprador recebe o bem digital e contesta como "não reconhecido" (10.4) ou "não recebido" | 3DS, coleta de evidências CE 3.0 (IP, device, login), aceite de termos, log de entrega |
| 4 | **Cartão roubado** | Loja (chargeback) e titular | Testes de cartão (card testing), compras de gift cards e keys, que são líquidos e revendáveis | Antifraude com score, velocidade, 3DS, retenção na primeira compra, limites por produto |
| 5 | **Pix + MED** (triangulação, falsa alegação de golpe) | Loja (devolução de valores já entregues) | Golpista anuncia barato em rede social e passa à vítima o **QR Pix da loja**. A loja recebe da vítima e entrega ao golpista. A vítima aciona o MED | **CPF do pagador = CPF da conta compradora**, QR dinâmico por pedido, retenção para pagador novo, registro de evidências para contestar o MED |
| 6 | **Comprovante Pix falso** | Loja / vendedor | Print editado de "Pix enviado" | Nunca liberar com base em print; liberar só com confirmação do PSP (webhook/API com endToEndId) |
| 7 | **Clone de site / falso suporte / falso intermediário** | Comprador e marca | Domínio parecido, perfil falso no Instagram ou Discord, "suporte" pedindo código 2FA | Lista pública de canais oficiais, DMARC p=reject, monitoramento de domínios parecidos (typosquatting), takedown, avisos no fluxo |
| 8 | **Negociação fora da plataforma** (chat) | Comprador; num marketplace, a plataforma perde a taxa e a proteção | Vendedor puxa a conversa para WhatsApp ou Pix direto | Filtro de telefone, chave Pix e links no chat; aviso de que só há garantia dentro da plataforma; penalidade |
| 9 | **Gift card: fraude e lavagem** | Loja, titular do cartão, vítimas de golpe | Comprar gift cards com cartão roubado ou com dinheiro de golpe e revender (a "liquidez") | Limites por CPF/dispositivo, KYC acima de certo valor, entregar código só depois da janela de risco, bloquear revenda em massa |
| 10 | **Tomada de conta (ATO) do cliente na loja** | Cliente (credenciais entregues expostas) e loja | Credential stuffing, phishing, SIM swap | 2FA/passkeys, checar senhas vazadas, step-up para revelar credenciais, alertas de novo dispositivo |
| 11 | **Bots / credential stuffing / scraping** | Loja | Teste de cartões, criação de contas em massa, scraping de preços e estoque | WAF + anti-bot (Turnstile), rate limit por IP/conta/dispositivo, verificação de e-mail e telefone |
| 12 | **Insider** (sócio, funcionário, suporte) | Loja e clientes | Ver ou copiar credenciais entregues, liberar pedidos, revender estoque | Cofre com criptografia, revelação só com dupla aprovação, logs imutáveis, menor privilégio, MFA por chave física |
| 13 | **Comprador toma a conta de volta ou pede reembolso e continua com ela** | Loja/vendedor | Depois do reembolso, o comprador segue usando a conta, ou troca dados e diz que não recebeu | Antes de reembolsar, exigir a devolução do acesso (re-handover) ou reverter os dados; reembolso só depois de a loja retomar o controle |
| 14 | **Golpe do "recuperador"** | Comprador | Terceiros cobram para "recuperar" contas | Comunicação educativa; suporte próprio rápido |

### Gaps
- Não encontrei casos jornalísticos documentados e datados (2022–2026) de **triangulação via Pix** em lojas de jogos nem de **comprovante Pix falso** nesse setor. A tipologia acima é inferida. Fica a confirmar com buscas como "golpe triangulação Pix" e "comprovante Pix falso loja".
- Não achei dados brasileiros recentes (2025–2026) sobre **lavagem de dinheiro com gift cards** ou sobre obrigações de PLD/COAF para revendedores de gift cards.
- Não achei relatos verificados de **fraude interna** (insider) em marketplaces de jogos.
- Não confirmei estatísticas de **credential stuffing** no setor de games (ex.: relatórios State of the Internet da Akamai) nesta sessão.
- O domínio phishdestroy.io sinalizou ggdbop.com e ggdlop.com como phishing de captura de credenciais, mas **sem ligação confirmada com a GGMax** ([PhishDestroy](https://phishdestroy.io/de/domain/ggdbop.com/)). Não incluí como exemplo de clone.

---

## 2. Que fraudes pesam mais numa loja com vendedor único do que num marketplace aberto

### Takeaway
Na loja com vendedor único **não existe um terceiro para absorver a perda**. Pullback, chargeback, MED e contas roubadas no estoque caem direto no caixa da loja. Marketplaces como GGMax, PlayerAuctions e Eldorado repassam boa parte desse risco ao vendedor com escrow e retenção de saldo. O risco maior da loja única está na **compra de estoque** (de quem a loja compra as contas) e no **pagamento**. Fraude de vendedor, negociação fora da plataforma e lavagem entre contas que combinam compra e venda só passam a importar quando a loja abrir para terceiros.

### Cited Findings
- A GGMax retém o saldo do vendedor (7 dias na tabela para contas; quase 30 dias para Supercell) e diz que seus termos permitem reter o saldo "para garantir a segurança de usuários que possam ser prejudicados". O risco é transferido ao vendedor. — [Reclame Aqui – retenção Supercell](https://www.reclameaqui.com.br/ggmax/retencao-abusiva-de-saldo-ggmax-promete-prazo-de-7-dias-e-retem-valor-por-30-dias-apos-venda-de-clash-royale_kCs-xdRIYG2PhgBG/); [Reclame Aqui – resposta citando os termos](https://www.reclameaqui.com.br/ggmax/dois-anos-de-frustracao-a-falta-de-solucao-da-ggmax-para-meus-problemas_cqiEMK2KtKXE45hI/) (a atribuição dessa frase a esta reclamação específica vem do resumo da busca)
- Na GGMax, depois de um banimento, o saldo retido é pago num prazo de 1 mês a partir do pedido de revisão, segundo uma vendedora. — [Reclame Aqui – banimento](https://www.reclameaqui.com.br/ggmax/solicitacao-de-liberacao-de-valor-retido-e-esclarecimento-sobre-banimento_BhXVNzNZ9PSIT6kf/)
- A PlayerAuctions segura o pagamento do comprador até a transferência da conta e a confirmação de recebimento. Em disputa, ela congela o reembolso enquanto o vendedor tenta recuperar a conta. — [CyberPost](https://cyberpost.co/is-it-safe-to-sell-account-on-playerauctions/); [Trustpilot PlayerAuctions](https://fi.trustpilot.com/review/playerauctions.com?page=3)
- Na Eldorado, o vendedor "ainda pode ser responsabilizado" depois do período de proteção. — [Eldorado – Account Warranty](https://intercom.help/eldoradogg/en/articles/8408988-account-warranty)

### Inferences
**Prioridade para a loja com vendedor único no lançamento** (do maior para o menor risco):
1. **Fornecimento contaminado**: contas compradas de jogadores que depois as recuperam, ou contas roubadas. Aqui a loja é a "compradora" exposta. É o risco mais caro, porque a loja perde o custo da conta, o reembolso ao cliente e a reputação. Mitigações: KYC de todo fornecedor (CPF + selfie), exigir e-mail de criação e recibos de compra, **carência interna** (ex.: segurar a conta 7–30 dias conforme a publisher antes de revender, como a GGMax faz com a Supercell) e **pagamento escalonado ao fornecedor** (parte na compra, o resto depois da carência). O contrato de compra deve trazer cláusula de responsabilidade e declaração de origem lícita.
2. **Chargeback e cartão roubado**: o cartão é o meio mais exposto em bens digitais de entrega imediata. Ver a seção 4.
3. **Pix com MED e triangulação**: o Pix "parece seguro" porque não tem chargeback, mas o MED 2.0 com autoatendimento e bloqueio em cadeia devolve valores à vítima. A loja que entregou o bem fica com o prejuízo.
4. **ATO de clientes e vazamento das credenciais entregues**: uma conta de cliente invadida dá acesso às credenciais já entregues e ao saldo. Como a segurança é o diferencial prometido, um único vazamento destrói a proposta de valor.
5. **Phishing e clones da marca**: crescem junto com a marca. Proteger desde o início (domínio, DMARC, canais oficiais).
6. **Insider**: com só dois sócios o risco é baixo, mas o cofre de credenciais deve nascer com logs e dupla aprovação, porque vai escalar com contratações de suporte.
7. **Bots**: card testing e criação de contas em massa. Barato de mitigar com WAF e anti-bot.

**Riscos que entram quando a loja abrir para vendedores terceiros:** vendedor que some depois de receber, anúncio falso, pullback feito pelo próprio vendedor, negociação fora da plataforma, compra combinada entre comprador e vendedor com cartão roubado para "sacar" (lavagem e cash-out), ATO de contas de vendedor para desviar saque, KYC de vendedor e regras de saque (retenção por categoria, reserva rolante). Aí faz sentido adotar escrow com retenção de saldo por categoria e publisher, como GGMax e PlayerAuctions.

**Aspecto jurídico:** como fornecedora direta, a loja responde pelo CDC (vício do produto e serviço). Num marketplace, a responsabilidade da plataforma como intermediária é discutida, mas a jurisprudência brasileira costuma enquadrar marketplaces na cadeia de fornecimento **[NV]**. Na prática, a loja única deve precificar garantia e reembolso no preço.

### Gaps
- Não achei dados quantitativos que comparem a perda por fraude entre lojas de vendedor único e marketplaces abertos de contas de jogos.
- Não verifiquei a jurisprudência atual sobre responsabilidade de marketplace pelo CDC nem decisões sobre venda de contas de jogos.

---

## 3. Entrega (handover) de contas: checklist por plataforma, evidências, garantia e seguro

### Takeaway
A boa prática do setor tem cinco pontos: entregar **acesso total com o e-mail original**, trocar **todos os vetores de recuperação** (e-mail, telefone, senha, 2FA, logins sociais vinculados, dispositivos e sessões), gravar **evidência em vídeo e logs**, dar uma **garantia com prazo definido por publisher** e **devolver o dinheiro só depois de retomar o controle da conta**. Não encontrei um produto de "seguro de conta" de terceiros oferecido por PlayerAuctions ou G2G. O que existe são garantias da própria plataforma (Eldorado: 5 dias) e retenções escalonadas (GGMax: 7 dias, ~30 para Supercell).

### Cited Findings
- No Free Fire, a recuperação de conta passa pelo **vínculo** (Google, Facebook, VK, ID). Entregar uma conta FF significa entregar ou trocar o vínculo. Conta sem vínculo, ou sem o login original, não é recuperável por terceiros. — [Free Fire Mania – recuperar conta (2026)](https://www.freefiremania.com.br/recuperar-conta-free-fire.html)
- Na verificação de entrega, recomenda-se vídeo do login e do inventário (prints são manipuláveis) e nunca repassar códigos de verificação. — [JivoChat](https://www.jivochat.com.br/blog/reviews/servicos/comprar-conta-de-free-fire-e-possivel.html)
- A Eldorado dá **garantia de 5 dias** em contas. Recuperação, banimento ou parada de funcionamento dentro do prazo cancela a venda com reembolso. Depois do prazo, sem devolução garantida, mas com investigação. — [Eldorado – Account Warranty](https://intercom.help/eldoradogg/en/articles/8408988-account-warranty)
- A PlayerAuctions tem um "after-sale protection process" com "evidence requirements" para o vendedor. — [Trustpilot PlayerAuctions](https://au.trustpilot.com/review/playerauctions.com?page=2)
- Segundo análise de terceiros, o escrow GamerProtect do G2G funciona bem para moeda virtual, mas deixa uma lacuna para a recuperação de conta depois que a janela fecha. As disputas seriam resolvidas em **crédito na loja**, não em dinheiro. **É fonte secundária e não consegui identificar exatamente qual dos resultados afirma isso.** — [Eneba Hub (provável)](https://www.eneba.com/hub/?p=104722)
- Os resumos de busca sobre PlayerAuctions e G2G não mencionam nenhum produto de seguro para recuperação de conta. A proteção termina quando fecha a janela de disputa. — [CyberPost](https://cyberpost.co/is-it-safe-to-sell-account-on-playerauctions/); [Trustpilot G2G](https://www.trustpilot.com/review/www.g2g.com?page=8)
- A GGMax tem uma "tabela oficial de prazos" de liberação por categoria (7 dias para "Vendas de contas"), mas aplica exceções por publisher (Supercell) que não aparecem nessa tabela. — [Reclame Aqui](https://www.reclameaqui.com.br/ggmax/retencao-abusiva-de-saldo-ggmax-promete-prazo-de-7-dias-e-retem-valor-por-30-dias-apos-venda-de-clash-royale_kCs-xdRIYG2PhgBG/)

#### [NV] Conhecimento prévio, a confirmar
- **[NV]** O Marco Civil da Internet (art. 15) obriga provedores de aplicação constituídos como PJ com fins econômicos a guardar registros de acesso por **6 meses**. Esses registros servem também de evidência em disputas. — [Planalto – Lei 12.965/2014](https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2014/lei/l12965.htm)
- **[NV]** O CDC art. 49 garante **direito de arrependimento de 7 dias** em compras fora do estabelecimento (internet). A aplicação a conteúdo digital já entregue é controversa. Os termos devem informar com clareza quando a entrega acontece e qual é a política. — [Planalto – CDC](https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm)

### Inferences
**Protocolo genérico de entrega (vale para todas as plataformas):**
1. **Antes de anunciar**, auditar a conta: e-mail de criação disponível? Recibos e primeiras compras disponíveis? Logins sociais vinculados? Histórico de banimentos? Gravar o inventário com data e hora.
2. **Na entrega**, entregar o e-mail original (ou trocar o e-mail dentro da plataforma para o e-mail do cliente). Trocar a senha, trocar ou remover o telefone, desativar o 2FA antigo e orientar o cliente a cadastrar o próprio, encerrar todas as sessões e dispositivos, remover formas de pagamento, gerar novos códigos de recuperação e desvincular as contas sociais e de console que não vão junto.
3. **Evidência**: gravação de tela do processo (feita pela loja), log do servidor com IP e dispositivo do cliente ao revelar a credencial, aceite eletrônico do "termo de recebimento" com checklist marcado pelo cliente e hash dos arquivos de evidência.
4. **Garantia por publisher**: prazos diferentes conforme a facilidade de recuperação via suporte. Publicar a tabela **inteira**, com as exceções. A GGMax não publica a exceção da Supercell, e isso gera reclamação.
5. **Reembolso condicionado**: devolver o dinheiro só depois de a loja recuperar o controle da conta ou confirmar que ela foi perdida (pullback ou ban), para evitar que o cliente receba o reembolso e continue com a conta.
6. **"Seguro" próprio**: uma garantia estendida paga (ex.: 30/90 dias) só é viável se a loja controlar todos os vetores de recuperação (e-mail de criação + recibos). Montar com reserva técnica (% da receita), sem seguradora. Não encontrei seguradoras brasileiras com esse produto.

**Checklist por plataforma.** Itens **[NV]**, que dependem das configurações atuais de cada publisher e precisam ser confirmados nas centrais de ajuda oficiais antes de virar procedimento operacional:

| Plataforma | Vetores de recuperação a neutralizar | Itens específicos | Risco de pullback (avaliação) |
|---|---|---|---|
| **Steam** | E-mail, telefone, senha, Steam Guard (app móvel), código de revogação "R" | Remover ou transferir o autenticador; "desautorizar todos os outros dispositivos"; **revogar a Steam Web API Key** (vetor clássico de golpe de troca); remover Family Sharing e formas de pagamento | **Alto**: o suporte costuma devolver a conta a quem prova as compras (cartão, keys). Os termos (SSA) proíbem transferir |
| **Riot (LoL/Valorant/TFT)** | E-mail, senha, 2FA por e-mail | Trocar o e-mail (exige código no e-mail atual); ativar a verificação de login; conferir o Riot ID | Médio/alto: a recuperação via e-mail de criação e dados de compra é possível |
| **Epic Games (Fortnite)** | E-mail, senha, 2FA (app/e-mail) | Revisar **contas conectadas** (PSN, Xbox, Nintendo, Steam), que têm restrições de troca de vínculo; encerrar sessões | Médio/alto |
| **Garena / Free Fire** | **Vínculo** (Google, Facebook, VK, Apple, X) | Entregar a conta vinculada com e-mail e telefone trocados, ou trocar o vínculo se o jogo permitir; recusar conta "convidado" | Alto se o vendedor mantiver acesso ao vínculo; o suporte da Garena não ajuda comprador |
| **Roblox** | E-mail, telefone, senha, 2-Step Verification, PIN | Encerrar todas as outras sessões; remover o PIN e os controles parentais antigos | Médio/alto: o suporte pode devolver ao dono original mediante recibos |
| **Supercell (Clash Royale/CoC/Brawl Stars)** | Supercell ID (e-mail) | Trocar o e-mail do Supercell ID; desvincular Game Center e Google Play antigos | **Muito alto**: o suporte devolve ao comprador original com base em recibos de compras no app. A GGMax retém ~30 dias |
| **Activision (CoD)** | Conta Activision + plataformas vinculadas | Restrições de desvincular plataformas (limite de trocas) | Médio/alto |
| **PSN** | E-mail de login, senha, 2FA | "Sair de todos os dispositivos"; desativar o console principal; remover o cartão | Médio |
| **Xbox / Microsoft** | E-mail, telefone, info de segurança, código de recuperação | Gerar novo código de recuperação; "sair em todos os lugares"; a substituição da info de segurança pode ter **período de espera de 30 dias**, uma janela de pullback | Médio/alto durante a janela |

### Gaps
- Não consegui ler as centrais de ajuda oficiais (Steam, Riot, Epic, Garena, Roblox, Supercell, Activision, Sony, Microsoft) para confirmar como cada uma troca e-mail e 2FA, quais períodos de espera aplica e quais critérios usa para devolver contas. A tabela acima é **[NV]**.
- Não confirmei o mecanismo **"Steam Trade Protection"** (meados de 2025), que permitiria reverter trocas de itens em até 7 dias. Pelo que sei, ele afeta diretamente a venda de skins e itens Steam (o vendedor pode reverter). É prioridade confirmar.
- Não achei produto de **seguro de conta de jogo** oferecido por seguradora no Brasil nem a política de garantia estendida paga da Eldorado ou da PlayerAuctions (as páginas não abriram).
- Não confirmei o conceito de mercado "conta full acesso" / "com e-mail de criação" no Brasil nem quanto ele vale a mais.

---

## 4. Defesas no pagamento: cartão (3DS, antifraude, chargeback) e Pix (MED, comprovantes)

### Takeaway
No cartão, a combinação recomendada para bens digitais de alto risco é antifraude com score (ClearSale, Konduto/Equifax-Boa Vista, Serasa Fraudnet ou o motor do adquirente), **3DS 2 obrigatório** acima de um certo valor ou para cliente novo, **regras de velocidade** e **coleta sistemática de evidências** (IP, device fingerprint, histórico de login) para usar o CE 3.0 da Visa. No Pix: QR dinâmico por pedido, liberação **só por webhook do PSP**, **CPF do pagador igual ao CPF verificado do comprador** e um processo para responder ao MED 2.0, que é obrigatório desde 02/02/2026 e tem autoatendimento.

### Cited Findings
- Games lideram as tentativas de fraude no e-commerce brasileiro no início do ano (5,4%, estudo da ClearSale de jan/2025). Gift cards mostram alta incidência em datas comerciais (12,2–12,4% em 2024). — [Monitor Mercantil](https://monitormercantil.com.br/janeiro-registrou-mais-de-r-200-milhoes-em-tentativas-de-fraude-no-e-commerce/); [ClearSale – Mapa da Fraude 2025](https://en.clear.sale/hubfs/MapaDaFraude2025_Report.pdf)
- CE 3.0 da Visa: reason code 10.4, vigente desde 15/04/2023. Exige histórico de transações anteriores não contestadas do mesmo titular com identificadores coincidentes (IP, device ID, login). Os limites variam entre as fontes. Uma delas afirma que a correspondência pode impedir a disputa antes de virar chargeback, mas essa afirmação é **forte, vem de fonte secundária e precisa ser checada nas regras da Visa**. — [Chargeback Gurus](https://www.chargebackgurus.com/blog/visa-compelling-evidence-3.0); [Nomupay](https://nomupay.com/compelling-evidence-3-0-your-new-chargeback-defence); [TaskUs](https://www.taskus.com/insights/how-visa-ce-3-0-helps-stop-friendly-fraud-protects-margins/)
- A Serasa Experian oferece o **Fraudnet** (solução antifraude e de dispositivo) e publica o Mapa da Fraude trimestral (1º tri/2026). — [Serasa Experian – Fraudnet](https://www.serasaexperian.com.br/solucoes/fraudnet); [Serasa Experian – Antifraude](https://www.serasaexperian.com.br/solucoes/antifraude/)
- A ClearSale publica o Mapa da Fraude anual (edição 2025 com dados de 2024), com o conteúdo completo atrás de cadastro. — [ClearSale – Mapa da Fraude](https://br.clear.sale/en/mapa-da-fraude)
- Os relatórios da Konduto (antigos, 2017–2020) diferenciam **tentativa** de fraude efetiva: a maioria das tentativas é bloqueada pelos sistemas de análise. Também citam como referência um índice controlado de chargeback entre 0,1% e 0,5% do faturamento. A atribuição exata dessa referência a um relatório específico não foi confirmada. — [Correio Braziliense (2018)](https://blogs.correiobraziliense.com.br/servidor/indice-de-tentativas-de-fraude-no-e-commerce-brasileiro-caiu-273-em-2018/)
- MED 2.0: obrigatório desde 02/02/2026 (Res. BCB 493/2025), autoatendimento digital desde 01/10/2025, bloqueio em cadeia de até 5 camadas, devolução em até 11 dias e mesmos critérios de monitoramento para contas PJ. — [Mercado Pago](https://www.mercadopago.com.br/blog/novas-regras-pix-contas-juridicas); [O Imparcial](https://oimparcial.com.br/noticias/2025/08/banco-central-moderniza-pix-e-med-permitira-devolucao-de-recursos-de-forma-totalmente-digital/); [O Povo](https://mais.opovo.com.br/jornal/economia/2025/11/24/golpe-no-pix-novo-mecanismo-permite-rastrear-toda-a-rota-do-dinheiro.html)
- Bloqueio cautelar de no máximo 72h (Res. BCB 1/2020, art. 39-B, §4º). — [Vade Mecum – jurisprudência](https://www.vademecumprevidenciario.com.br/jurisprudencia/eme/483.0755.0649.2899)

#### [NV] Conhecimento prévio, a confirmar
- **[NV]** No 3-D Secure 2, uma transação autenticada com sucesso normalmente transfere ao emissor a responsabilidade por chargebacks de **fraude** (liability shift). Ela **não** protege contra disputas de "produto não recebido" ou "não conforme". Por isso a evidência de entrega continua necessária.
- **[NV]** As bandeiras têm programas de monitoramento de comerciantes com índice excessivo de disputas e fraudes. A Visa unificou os seus no **VAMP** (Visa Acquirer Monitoring Program) a partir de 2025. Estourar os limites gera multas e pode levar ao descredenciamento. Os limites atuais precisam ser confirmados com o adquirente.
- **[NV]** Pelas regras do BC, o MED cobre suspeita de **fraude** e **falha operacional**, não "desacordo comercial". Mesmo assim, o autoatendimento reduz o atrito para quem alega golpe sem ter sofrido um. A loja precisa registrar a entrega para contestar junto ao PSP recebedor. Confirmar no Regulamento do Pix (Res. BCB 1/2020, consolidada) e no Manual do DICT.
- **[NV]** Fornecedores de antifraude e pagamento no Brasil: ClearSale ([br.clear.sale](https://br.clear.sale)), Konduto, hoje no grupo Boa Vista/Equifax ([konduto.com](https://www.konduto.com)), Serasa Experian Fraudnet, CAF ([caf.io](https://www.caf.io)), além dos motores próprios de gateways e adquirentes (Pagar.me/Stone, Mercado Pago, Adyen, Stripe Radar, Cielo, PagBank). A maioria oferece 3DS 2 e device fingerprinting embutidos.

### Inferences
**Playbook de pagamentos para a loja:**
- **Cartão**
  - Antifraude com score em **todas** as transações. Revisão manual de pedidos acima de um valor de referência (ex.: o ticket médio da categoria × 3) e de gift cards e keys.
  - **3DS 2** sempre na primeira compra, acima de um certo valor e em gift cards. Fricção aceitável num nicho em que segurança é o diferencial.
  - **Regras de velocidade**: N cartões por conta, CPF ou dispositivo em 24h; N tentativas negadas antes de bloquear; limite de valor diário para conta nova; bloqueio de cartões pré-pagos e estrangeiros em produtos líquidos (gift cards).
  - **Retenção para cliente novo**: entregar contas e gift cards de alto valor com atraso (ex.: 2–24h) e revisão quando o cliente não tem histórico.
  - **Evidências para CE 3.0 e contestação**: guardar IP, device ID, user-agent, histórico de logins, aceite dos termos, log de revelação da credencial e e-mails de entrega. Montar um "pacote de disputa" automático por pedido.
  - Monitorar o índice de chargeback por método, produto e publisher, e manter a meta abaixo do limite das bandeiras e do adquirente.
- **Pix**
  - **QR dinâmico com txid único e expiração curta** por pedido. Nunca chave estática.
  - Liberar **somente com confirmação do PSP** (webhook ou consulta à API com endToEndId e valor). Nunca com print de comprovante.
  - **CPF do pagador = CPF da conta compradora** (verificado no KYC). Quando o PSP devolve o CPF ou nome do pagador no webhook, divergência significa bloqueio automático: é o principal antídoto contra triangulação. Pagamento de terceiros é estornado e cancelado.
  - "**Pix-only para novos usuários**" reduz chargeback, mas **não elimina o risco** por causa do MED 2.0. Combinar com o CPF batendo e com retenção acima de um valor.
  - **Processo para MED**: quem recebe a notificação de MED é o PSP da loja. Ter um playbook para responder com evidências em poucas horas, conta PJ dedicada e capital de giro para cobrir bloqueios cautelares de até 72h.
- **Restringir meios de alto risco**: boleto tem risco baixo de fraude, mas é lento. Cartão de terceiros e carteiras sem KYC devem ter limites mais baixos ou ser bloqueados para gift cards e keys.

### Gaps
- Não confirmei o texto da **Res. BCB 493/2025**, o prazo de 80 dias do autoatendimento nem os prazos de análise do recebedor no MED 2.0 (bcb.gov.br não respondeu).
- Não achei dados atuais (2025–2026) de taxa de chargeback em games no Brasil nem preços e planos de ClearSale, Konduto ou Serasa para pequenas lojas.
- Não confirmei quais PSPs brasileiros devolvem o CPF ou nome completo do pagador no webhook Pix (varia por PSP) nem se há recurso nativo de "Pix só do mesmo titular".
- Não verifiquei a taxa de adoção nem a fricção do 3DS 2 no Brasil.

---

## 5. Identidade: KYC (documento + selfie), validação de CPF e checagem de idade

### Takeaway
KYC em camadas: e-mail e telefone verificados para todos; CPF validado (situação cadastral, nome e data de nascimento) para comprar; documento + selfie com prova de vida para alto valor, gift cards, **todo fornecedor ou vendedor** e saques. Biometria é dado pessoal **sensível** pela LGPD. A lição dos incidentes de 2025 é reter o mínimo de imagens de documentos e escolher fornecedores que devolvam só o resultado da checagem. O ECA Digital (Lei 15.211/2025) aumenta a pressão por verificação de idade em serviços digitais acessados por menores **[NV]**.

### Cited Findings
- A Serasa Experian oferece soluções antifraude e de identidade (Fraudnet) para empresas brasileiras. — [Serasa Experian – Fraudnet](https://www.serasaexperian.com.br/solucoes/fraudnet)
- Nesta sessão não consegui verificar, com fonte aberta, as documentações de unico, idwall, Serpro Datavalid ou CAF. Ver Gaps.

#### [NV] Conhecimento prévio, a confirmar
- **[NV]** Fornecedores brasileiros de KYC e biometria: **unico** (unico check, [unico.io](https://unico.io)), **idwall** ([idwall.co](https://idwall.co)), **CAF** ([caf.io](https://www.caf.io)), **Serpro Datavalid** (validação biométrica e cadastral contra bases governamentais), **BigDataCorp** ([bigdatacorp.com.br](https://bigdatacorp.com.br)) e **Serasa Experian**. A validação de CPF (situação cadastral, nome, data de nascimento) é feita pelos produtos de consulta do Serpro ou por bureaus.
- **[NV]** LGPD: dado **biométrico** é dado pessoal sensível (art. 5º, II), com bases legais restritas (art. 11). Incidentes de segurança devem ser comunicados à ANPD e aos titulares (art. 48). O regulamento de comunicação de incidentes da ANPD (Res. CD/ANPD nº 15/2024) fixa prazo de 3 dias úteis. — [Planalto – LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- **[NV]** Código Civil: menores de 16 anos são absolutamente incapazes (art. 3º) e os de 16 a 18, relativamente incapazes (art. 4º). Por isso compras feitas por menores sem assistência são anuláveis, o que vira risco de reembolso e chargeback do tipo "foi meu filho". — [Planalto – Código Civil](https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilado.htm)
- **[NV]** **ECA Digital (Lei 15.211/2025)**, sancionado em set/2025 e com vigência a partir de mar/2026: exige mecanismos confiáveis de verificação de idade (sem bastar a autodeclaração) para conteúdos e serviços impróprios para menores e restringe **loot boxes** em jogos voltados a crianças e adolescentes. Confirmar o texto, a vigência e a regulamentação da ANPD. — [Planalto – Lei 15.211/2025 (URL a confirmar)](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/L15211.htm)
- **[NV]** **Incidente do Discord (out/2025)**: um prestador terceirizado de atendimento foi comprometido, e imagens de documentos de identidade enviadas em recursos de verificação de idade (na casa de ~70 mil usuários, segundo o comunicado do Discord) podem ter sido expostas. Lição direta para KYC: não guardar documentos no helpdesk e controlar os subprocessadores.

### Inferences
**Desenho de KYC em camadas (proporcional ao risco):**
| Camada | Quando | Checagens |
|---|---|---|
| 0 | Cadastro | E-mail verificado, telefone verificado por SMS ou WhatsApp, device fingerprint, Turnstile |
| 1 | 1ª compra | CPF válido e regular, nome e data de nascimento batendo, **18+** (ou responsável identificado), CPF do pagador Pix igual |
| 2 | Compra acima de R$ X, gift cards, mudança de e-mail ou telefone, saque | Documento + selfie com prova de vida (unico, idwall, CAF, Datavalid) |
| 3 | **Fornecedores de contas** (agora) e **vendedores** (no futuro) | Camada 2 + conta bancária no mesmo CPF/CNPJ + contrato com declaração de origem lícita |

- **Idade**: a política mais simples e defensável é **vender só para maiores de 18**, ou exigir o CPF do responsável e pagamento no CPF dele. Isso reduz reembolsos de "compra feita pelo filho" e o risco regulatório do ECA Digital.
- **Minimizar dados**: guardar o resultado da checagem (aprovado, score, id da transação no fornecedor) em vez das imagens; nunca anexar documentos em tickets de suporte; contrato com o fornecedor (operador LGPD) com cláusulas de segurança e de exclusão.

### Gaps
- Não consegui confirmar preços, SLA ou integrações de unico, idwall, CAF ou Serpro Datavalid nem a disponibilidade para pequenas empresas.
- Não confirmei o texto final do ECA Digital, sua vigência exata nem se ele se aplica a marketplaces de contas e itens (e não só a jogos e redes sociais).
- Não confirmei o número exato de usuários afetados no incidente do Discord nem o nome do prestador envolvido.

---

## 6. Segurança da plataforma e da aplicação, e incidentes no setor (2022–2026)

### Takeaway
As falhas que mais destruiriam a confiança num site desse tipo são: **controle de acesso quebrado** (IDOR que permite ver credenciais entregues a outro cliente), **ATO de clientes**, **comprometimento do painel admin ou de um prestador terceirizado** e **engenharia social contra a equipe**. A defesa central é um **cofre de credenciais** (criptografia em envelope, revelação única com step-up, logs imutáveis, dupla aprovação para a equipe), combinado com passkeys/2FA, WAF/anti-bot e um painel admin isolado atrás de Zero Trust e chaves FIDO2.

### Cited Findings
- Não consegui ler páginas primárias de segurança de aplicações nem relatórios de incidentes nesta sessão (falha de DNS da ferramenta e orçamento de buscas esgotado). Os itens abaixo são **[NV]**.

#### [NV] Conhecimento prévio, a confirmar
- **[NV] OWASP Top 10:2025** (publicado em nov/2025): A01 Broken Access Control; A02 Security Misconfiguration; A03 Software Supply Chain Failures; A04 Cryptographic Failures; A05 Injection; A06 Insecure Design; A07 Authentication Failures; A08 Software or Data Integrity Failures; A09 Security Logging and Alerting Failures; A10 Mishandling of Exceptional Conditions. — [OWASP Top 10:2025](https://owasp.org/Top10/2025/)
- **[NV]** O OWASP ASVS serve de checklist verificável. O projeto "OWASP Automated Threats to Web Applications" cataloga ameaças de bots (credential stuffing, card cracking, scalping etc.). — [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/); [OWASP Automated Threats](https://owasp.org/www-project-automated-threats-to-web-applications/)
- **[NV]** O NIST SP 800-63B (rev. 4, 2025) recomenda checar senhas contra listas de senhas comprometidas, não exigir troca periódica e preferir autenticadores resistentes a phishing (passkeys/FIDO2). — [NIST SP 800-63B-4](https://pages.nist.gov/800-63-4/sp800-63b.html)
- **[NV]** Ferramentas: Cloudflare WAF, Bot Management e **Turnstile** (CAPTCHA gratuito e sem fricção); API Pwned Passwords do HIBP (k-anonymity) para checar senhas vazadas. — [Cloudflare Turnstile](https://www.cloudflare.com/products/turnstile/); [HIBP Pwned Passwords](https://haveibeenpwned.com/API/v3#PwnedPasswords)
- **[NV] Incidentes 2022–2026 e lições** (confirmar datas e números):
  - **Riot Games (jan/2023)**: engenharia social contra o ambiente de desenvolvimento; código-fonte de LoL/TFT e de um anticheat legado roubado; resgate de US$ 10 mi recusado. *Lição: treinamento contra engenharia social e MFA resistente a phishing para a equipe.*
  - **CS.MONEY (abr/2023)**: ataque aos bots de troca levou cerca de 20 mil itens (~US$ 6 mi em skins). *Lição: estoque de itens em custódia é uma "hot wallet"; segregar, limitar e monitorar.*
  - **Roblox (2023)**: vazamento de dados de alguns milhares de participantes da Roblox Developer Conference (2017–2020). *Lição: dados de eventos e sistemas periféricos também vazam.*
  - **Steam (mai/2025)**: alegação de vazamento de ~89 milhões de registros com códigos de 2FA por SMS antigos. A Valve negou violação dos próprios sistemas e não havia senhas. *Lição: 2FA por SMS é fraco; preferir app ou passkey.*
  - **Discord (out/2025)**: comprometimento de um prestador de atendimento com exposição de documentos de identidade. *Lição: risco de terceiros e retenção de documentos de KYC.*

### Inferences
**OWASP aplicado a uma loja de contas e gift cards:**
- **A01 Controle de acesso**: todo acesso a pedido, credencial ou código checa o dono no servidor (sem IDs sequenciais expostos, com UUID e autorização por objeto). Testes automáticos de IDOR no CI.
- **A04 Criptografia**: credenciais e códigos entregues ficam em **criptografia em envelope** (uma DEK por item, KEK em KMS gerenciado: AWS KMS, GCP KMS ou Vault). Nunca em texto puro no banco, em logs ou no e-mail.
- **A07 Autenticação**: passkeys (WebAuthn) como opção principal; 2FA por TOTP; checagem de senha vazada; bloqueio progressivo; alerta de novo dispositivo; **step-up** (reautenticação) para revelar uma credencial, trocar e-mail ou telefone, ou sacar.
- **A09 Logs e alertas**: logs de auditoria **imutáveis** (append-only, enviados para fora do servidor) de toda revelação de credencial, ação admin e mudança de dados. Guardar pelo menos 6 meses (Marco Civil) **[NV]**. Alertas em tempo real para revelações em massa.
- **A03 Cadeia de suprimentos**: dependências fixadas (lockfile), Dependabot ou Renovate, SCA; reduzir scripts de terceiros no checkout (risco de skimming).
- **A10 Exceções**: falhas do webhook Pix ou do antifraude devem **negar por padrão** (fail closed), nunca entregar o produto quando a verificação dá erro.

**Cofre de credenciais e códigos (o principal diferencial técnico):**
1. Criptografia em envelope com KMS, rotação de chaves e separação entre quem tem acesso ao banco e quem tem acesso à KEK.
2. **Revelação única** ou por tempo limitado: o cliente vê a credencial depois do pagamento confirmado + step-up. A página registra IP, dispositivo e data/hora. Opcionalmente, marca d'água com o ID do cliente no código ou no print.
3. **A equipe não vê credenciais** por padrão. Acesso "break-glass" com justificativa, **dupla aprovação** (os dois sócios) e alerta.
4. Expiração: depois de X dias da entrega, apagar ou reembaralhar a credencial armazenada (o cliente já trocou a senha). Isso reduz o impacto de um vazamento.

**Painel admin e equipe:**
- Admin num domínio ou subdomínio separado atrás de **Zero Trust** (ex.: Cloudflare Access) ou VPN, com **chaves FIDO2** obrigatórias, sem contas compartilhadas, com menor privilégio (papéis: suporte, financeiro, estoque) e log de todas as ações.
- Proteção contra engenharia social: o suporte **nunca** pede senha nem código 2FA. Processo verificado para trocar e-mail ou telefone de cliente (com KYC e período de espera).

**Bordas:** WAF + anti-bot, rate limiting por IP, conta, dispositivo e CPF em login, cadastro, checkout e revelação; Turnstile no cadastro e no checkout; bloqueio de e-mails descartáveis.

**Anti-phishing da marca:** SPF, DKIM e **DMARC p=reject**; registrar variações óbvias do domínio; monitorar domínios parecidos e perfis falsos; página "Canais oficiais"; avisos dentro do produto ("nunca pediremos seu código").

### Gaps
- Não consegui confirmar o OWASP Top 10:2025 na fonte nem os detalhes, datas e números dos incidentes listados.
- **Não encontrei registro de vazamento de dados ou incidente na GGMax** nem em outros marketplaces brasileiros de contas (2022–2026). A ausência de resultado não prova que não houve incidente.
- Não verifiquei incidentes específicos em G2A, Eneba, Kinguin, G2G, PlayerAuctions ou Eldorado.

---

## 7. O que a GGMax e os líderes globais fazem em segurança, e lacunas que um entrante pode explorar

### Takeaway
GGMax, PlayerAuctions, G2G e Eldorado usam o mesmo modelo: **escrow e retenção de saldo + garantia curta + mediação**. As reclamações públicas se concentram em três pontos: retenções maiores que as anunciadas e **exceções não documentadas** (GGMax e Supercell), **atendimento lento ou sem resposta** (a GGMax respondeu menos de 50% das reclamações no Reclame Aqui no 1º semestre de 2026) e **reembolso negado depois que a garantia acaba ou pago em crédito** (Eldorado e G2G). As lacunas que um entrante pode ocupar: **transparência total** de prazos e garantias por publisher, **reembolso em dinheiro**, **suporte rápido e humano**, **segurança visível ao cliente** (passkeys, cofre, canais oficiais) e **estoque verificado** (procedência da conta).

### Cited Findings
- **GGMax, reputação**: menos de 50% das reclamações respondidas, com tempo médio de resposta de 6 horas, de 01/01/2026 a 30/06/2026. — [Reclame Aqui – GGMAX](https://www.reclameaqui.com.br/empresa/ggmax/lista-reclamacoes/)
- **GGMax, retenção**: tabela de 7 dias para contas, mas ~30 dias para Supercell sem estar documentado. A reclamação ficou sem solução. — [Reclame Aqui](https://www.reclameaqui.com.br/ggmax/retencao-abusiva-de-saldo-ggmax-promete-prazo-de-7-dias-e-retem-valor-por-30-dias-apos-venda-de-clash-royale_kCs-xdRIYG2PhgBG/)
- **GGMax, banimento com saldo**: uma vendedora banida sem aviso viu no painel uma data de liberação que não foi cumprida. Depois, recebeu prazo de 1 mês a partir do pedido de revisão. — [Reclame Aqui](https://www.reclameaqui.com.br/ggmax/solicitacao-de-liberacao-de-valor-retido-e-esclarecimento-sobre-banimento_BhXVNzNZ9PSIT6kf/)
- **GGMax, domínios parecidos** com reputações distintas (incluindo um recente, ggmaxpro.life). — [Site Confiável](https://www.siteconfiavel.com.br/site/ggmaxpro-life)
- **Eldorado**: garantia de 5 dias em contas; reembolso se houver recuperação ou ban no prazo; investigação depois disso. Relatos de pullback após 5 dias e de ban depois de disputa bancária. — [Eldorado – Account Warranty](https://intercom.help/eldoradogg/en/articles/8408988-account-warranty); [Trustpilot Eldorado.gg](https://au.trustpilot.com/review/eldorado.gg?page=4); [Plisio – review Eldorado](https://plisio.net/cybersecurity/eldorado-gg-review)
- **G2G**: escrow (GamerProtect) com janela de confirmação. Disputas pagas em crédito na loja (fonte secundária). Reembolso negado depois de o pedido ser marcado como concluído. — [Trustpilot G2G](https://www.trustpilot.com/review/www.g2g.com?page=8); [Eneba Hub (provável fonte)](https://www.eneba.com/hub/?p=104722)
- **PlayerAuctions**: segura o pagamento até a confirmação; tem processo de proteção pós-venda com requisitos de evidência; congela o reembolso durante a disputa. — [CyberPost](https://cyberpost.co/is-it-safe-to-sell-account-on-playerauctions/); [Trustpilot PlayerAuctions](https://au.trustpilot.com/review/playerauctions.com?page=2)

### Inferences
**Diferenciais de segurança que um entrante pode tornar visíveis (do mais barato ao mais caro):**
1. **Tabela pública de garantia e prazos por publisher, com todas as exceções**, ataca direto a principal reclamação contra a GGMax.
2. **"Conta com procedência"**: selo indicando que a conta tem e-mail de criação e recibos e passou pela carência interna sem pullback. A loja única controla o estoque e consegue fazer isso, coisa que um marketplace aberto não consegue.
3. **Reembolso em dinheiro (Pix) e SLA de resposta publicado** (ex.: 1h em horário comercial), em contraste com crédito na loja (G2G) e baixa taxa de resposta (GGMax no Reclame Aqui).
4. **Entrega assistida e gravada** (handover guiado, com checklist marcado pelo cliente e vídeo), o que reduz disputas e serve de evidência.
5. **Segurança da conta do cliente**: passkeys, 2FA obrigatório para revelar credenciais, alertas de login e cofre com revelação única. Comunicar isso numa página "Como protegemos você".
6. **Anti-golpe**: página de canais oficiais, DMARC, verificação de domínio, botão "isso é golpe?" no chat e educação sobre o falso intermediário.
7. **Garantia estendida opcional** (30/90 dias) para publishers de baixo risco, financiada por reserva técnica.
8. **Reputação**: responder 100% no Reclame Aqui desde o 1º dia e buscar o selo RA1000. Pesa muito na decisão do consumidor brasileiro **[NV]**.

### Gaps
- Não consegui acessar a central de ajuda nem os termos da GGMax (falha de DNS da ferramenta). Não verifiquei se a GGMax exige **KYC com selfie** de vendedores, oferece **2FA** ou **passkeys**, tem **garantia de contas** formal ou **seguro**, nem quais taxas cobra. Também não confirmei qual dos domínios (ggmax.com.br ou ggmax.com) é o oficial.
- Não verifiquei as políticas oficiais de G2G (GamerProtect), PlayerAuctions (Account Recovery Protection / garantia estendida) e Eldorado (garantia estendida paga), nem o que fazem Z2U, Eneba, G2A e U7BUY.
- Não achei análises independentes (jornalísticas) de segurança comparando marketplaces brasileiros (GGMax, Hype Games, DFG etc.).

---

## 8. Checklist de segurança priorizado para o MVP (loja com vendedor único, preparada para abrir a terceiros)

### Takeaway
Antes de lançar (P0), priorizar o que evita **perda direta de caixa** e **vazamento de credenciais**: procedência do estoque com carência, antifraude + 3DS + evidências no cartão, Pix com QR dinâmico, webhook e CPF batendo, cofre de credenciais com revelação controlada, 2FA/passkeys e step-up, WAF/anti-bot, admin isolado com FIDO2, termos claros e tabela de garantia pública. Depois (P1/P2), automação de disputas, KYC biométrico mais amplo, monitoramento de marca e a infraestrutura de marketplace (escrow, KYC de vendedor, filtro de chat).

### Cited Findings
- A retenção por publisher (GGMax: 7 dias para contas, ~30 para Supercell) e a garantia de 5 dias (Eldorado) são as referências de mercado para prazos. — [Reclame Aqui](https://www.reclameaqui.com.br/ggmax/retencao-abusiva-de-saldo-ggmax-promete-prazo-de-7-dias-e-retem-valor-por-30-dias-apos-venda-de-clash-royale_kCs-xdRIYG2PhgBG/); [Eldorado – Account Warranty](https://intercom.help/eldoradogg/en/articles/8408988-account-warranty)
- O CE 3.0 depende de dados históricos coletados antes da disputa, por isso a coleta precisa começar no dia 1. — [Nomupay](https://nomupay.com/compelling-evidence-3-0-your-new-chargeback-defence)
- O MED 2.0 é obrigatório desde 02/02/2026, com autoatendimento e bloqueio em cadeia. O Pix não é "sem estorno". — [Mercado Pago](https://www.mercadopago.com.br/blog/novas-regras-pix-contas-juridicas); [O Povo](https://mais.opovo.com.br/jornal/economia/2025/11/24/golpe-no-pix-novo-mecanismo-permite-rastrear-toda-a-rota-do-dinheiro.html)
- Games e gift cards estão entre as categorias mais visadas no Brasil. — [Monitor Mercantil](https://monitormercantil.com.br/janeiro-registrou-mais-de-r-200-milhoes-em-tentativas-de-fraude-no-e-commerce/); [ClearSale – Mapa da Fraude 2025](https://en.clear.sale/hubfs/MapaDaFraude2025_Report.pdf)

### Inferences
**P0: obrigatório antes do lançamento**
1. [ ] **Procedência do estoque**: KYC (CPF + selfie) de todo fornecedor; contrato de cessão com declaração de origem lícita e responsabilidade por recuperação; exigir e-mail de criação e recibos; **carência interna por publisher** antes de revender; pagamento ao fornecedor parcelado e condicionado à carência.
2. [ ] **Protocolo de entrega por plataforma** (seção 3), com checklist marcado pelo cliente, gravação e log.
3. [ ] **Termos de uso e política de garantia públicos**: prazo por publisher (com todas as exceções), o que a garantia cobre (pullback, ban, inacessível), reembolso condicionado à devolução do acesso, posição sobre o art. 49 do CDC para conteúdo digital, proibição de compra por menores sem responsável e aviso de que os termos das publishers proíbem a venda (risco de ban).
4. [ ] **Cartão**: gateway com antifraude e **3DS 2** (sempre na 1ª compra e em gift cards e keys); regras de velocidade; bloqueio de pré-pago e internacional em gift cards; coleta de IP, dispositivo e login para CE 3.0.
5. [ ] **Pix**: QR dinâmico com txid por pedido; liberação **só por webhook ou API do PSP**; **CPF do pagador = CPF do cliente**; estorno automático de Pix de terceiros; conta PJ dedicada; playbook de resposta ao MED.
6. [ ] **Retenção para cliente novo** em pedidos de alto valor (entrega com atraso e revisão manual).
7. [ ] **Cofre de credenciais**: criptografia em envelope (KMS), revelação só depois do pagamento confirmado + step-up, log de cada revelação, a equipe não vê sem dupla aprovação, expiração ou apagamento depois da janela de garantia.
8. [ ] **Autenticação de clientes**: e-mail e telefone verificados, TOTP ou passkey (2FA obrigatório para revelar credenciais e sacar saldo), checagem de senha vazada, alerta de novo dispositivo, encerramento de sessões.
9. [ ] **Borda**: Cloudflare (ou similar) com WAF, rate limiting, Turnstile em cadastro, login e checkout, e bloqueio de e-mail descartável.
10. [ ] **Admin**: subdomínio separado atrás de Zero Trust ou VPN, **FIDO2 obrigatório** para os dois sócios, papéis com menor privilégio, logs imutáveis.
11. [ ] **Testes de controle de acesso** (IDOR) em pedidos e credenciais; dependências fixadas e monitoradas; segredos fora do código.
12. [ ] **Anti-phishing**: SPF, DKIM e DMARC p=reject; página "canais oficiais"; o suporte nunca pede senha nem código (aviso fixo no chat e nos e-mails).
13. [ ] **LGPD básico**: política de privacidade, registro das operações, contrato com operadores (KYC, antifraude), plano de resposta a incidentes (comunicação à ANPD) **[NV prazo]** e guarda de logs de acesso por 6 meses (Marco Civil) **[NV]**.
14. [ ] **Maioridade**: vender só para maiores de 18 (data de nascimento validada pelo CPF) ou com responsável identificado.

**P1: primeiros 90 dias**
15. [ ] KYC com documento + selfie (unico, idwall, CAF ou Datavalid) acima de um valor de referência, para gift cards e para trocar e-mail ou telefone.
16. [ ] Pacote automático de evidências por pedido para chargebacks e MED; dashboard com índice de chargeback e MED por meio de pagamento, produto e publisher.
17. [ ] Monitoramento de marca: domínios parecidos, perfis falsos em Instagram, Discord e TikTok, processo de takedown.
18. [ ] Passkeys como login principal; step-up com passkey.
19. [ ] Garantia estendida opcional (reserva técnica) para publishers de menor risco.
20. [ ] Teste de invasão externo antes de escalar a mídia paga; programa simples de divulgação responsável (security.txt).
21. [ ] Responder 100% das reclamações no Reclame Aqui e publicar o SLA de suporte.

**P2: antes de abrir para vendedores terceiros**
22. [ ] Escrow com retenção de saldo por categoria e publisher (publicada), reserva rolante para vendedores novos e saque só para conta no mesmo CPF/CNPJ do KYC.
23. [ ] KYC obrigatório de vendedor (camada 3) e limites por reputação.
24. [ ] Filtro no chat contra negociação fora da plataforma (telefone, chave Pix, links externos) e alertas educativos.
25. [ ] Detecção de conluio (comprador e vendedor ligados por dispositivo, IP ou CPF) e de cash-out com cartão roubado.
26. [ ] Mediação com prazos e evidências padronizados (modelo PlayerAuctions/Eldorado, só que com reembolso em dinheiro).
27. [ ] Avaliar as obrigações de PLD/COAF e o enquadramento regulatório do saldo em conta (possível arranjo de pagamento) antes de manter saldo de terceiros **[NV, consultar advogado]**.

### Gaps
- Os valores de referência (R$ X para KYC, prazos de carência por publisher, limites de velocidade) dependem do mix de produtos e do apetite a risco. Não há benchmark público do setor; precisam ser calibrados com os dados dos primeiros meses.
- O enquadramento regulatório de um marketplace com saldo em conta (Lei 12.865/2013, arranjos de pagamento; PLD) não foi pesquisado nesta sessão.
- Vários itens do checklist dependem de fatos **[NV]**: ECA Digital, prazo de comunicação à ANPD, detalhes do MED 2.0 e procedimentos de cada publisher. Confirmar antes de transformar em política.
