# UX, funcionalidades, retenção e crescimento de marketplaces gamer (GGMax, concorrentes BR e líderes globais)

> **Nota de método (12/10/2026):** a ferramenta de leitura de páginas (WebFetch) falhou com erro de DNS para **todos** os domínios testados (ggmax.com.br, similarweb.com, semrush.com, support.google.com e até wikipedia.org). Por isso **não foi possível navegar pelas páginas** (home, anúncio, checkout) dos sites. Tudo abaixo vem de resultados de busca (títulos, trechos e resumos de páginas indexadas), cujas URLs estão citadas. O orçamento de buscas da sessão também se esgotou antes de cobrir políticas de anúncios da Meta, concorrentes brasileiros menores e campanhas de influenciadores. Esses pontos estão listados em "Lacunas". Os dados de tráfego são estimativas de terceiros (Semrush/Similarweb) e divergem entre si.

## 1. Anatomia de UX (home, navegação, busca/filtros, página do anúncio, checkout, pós-compra, mobile): o que o GGMax faz bem e mal

### Takeaway
O GGMax é um marketplace C2C com intermediação de pagamento (escrow). A UX dele foi feita para o lado do vendedor: anunciar é gratuito, a visibilidade é vendida em planos (Ouro e Diamante ganham destaque na home e na busca), há anúncios dinâmicos com estoque automático, e o catálogo é muito amplo, chegando a cursos e serviços de criação de sites. O pós-compra gira em torno do chat do pedido e de prazos de liberação de 4 a 7 dias. O oposto disso é o padrão Codashop: compra sem login, em três passos, com o ID do jogador e crédito imediato.

### Cited Findings
**GGMax: fluxo e estrutura**
- No fluxo de compra, o comprador paga à GGMAX, que é a intermediadora. O vendedor entrega, o comprador confirma o recebimento e só então a plataforma libera o pagamento ao vendedor. — [Como funciona - GGMAX](https://ggmax.com.br/como-funciona); [FAQ - GGMAX](https://ggmax.com.br/faq)
- Anunciar é gratuito, e a tarifa só é cobrada se houver venda. — [Tarifas e prazos - GGMAX](https://ggmax.com.br/tarifas-e-prazos)
- Planos de vendedor: Prata (9,99% sobre a venda), Ouro (11,99%) e Diamante (12,99%). — [Termos de uso - GGMAX](https://www.ggmax.com.br/termos-de-uso)
- O Prata tem só o anúncio básico. O Ouro ganha "destaque na página principal" e mais visibilidade. O Diamante ganha destaque na página principal **e** nas pesquisas. Em outras palavras, a vitrine da home e o ranking da busca são, em parte, espaço pago. — [Tarifas e prazos - GGMAX](https://ggmax.com.br/tarifas-e-prazos)
- Respondendo a um vendedor Diamante que disse não ver seu destaque, a GGMAX afirmou que "os anúncios são ordenados pelo filtro escolhido pelo usuário". Isso indica que existe ordenação/filtro na listagem e que o destaque pago depende da ordenação escolhida pelo comprador (caso isolado, sem data exata, aprox. 2023/2024). — [Reclame Aqui - Anúncio Diamante não respeitado](https://www.reclameaqui.com.br/ggmax/anuncio-diamante-nao-respeitado_dRIaluHQa0wREW1d/)
- Existem "Anúncios dinâmicos" e "Estoque Automático", que permitem a entrega automatizada de itens com estoque (artigo do blog oficial). — [Blog GGMAX - Anúncios dinâmicos e Estoque Automático](https://ggmax.com.br/blog/anuncios-dinamicos-e-estoque-automatico-como-configurar-meu-anuncio)
- A URL e o título das páginas de anúncio seguem a hierarquia "Título - Jogo - Categoria - GGMAX", por exemplo "Elojob acessível - Valorant - Elojob" e "PONTOS STEAM - Steam - Outros". — [GGMAX anúncio Elojob](https://ggmax.com.br/anuncio/elojob-acessivel); [GGMAX anúncio Pontos Steam](https://ggmax.com.br/anuncio/pontos-steam-q5xy60ie)
- O catálogo vai além de jogos e inclui categorias como "Serviços Digitais" ("EU FAÇO O SEU SITE!") e "Cursos e Treinamentos", com anúncios do tipo "Do Zero ao Lucro na GGMAX", "Ebook GGmax: Otimize Seus Anúncios" e "DESTAQUE SEU ANÚNCIO E VENDA MUITO MAIS" (este dentro de Brawl Stars). — [GGMAX - Eu faço o seu site](https://www.ggmax.com.br/anuncio/eu-faco-o-seu-site); [GGMAX - Do Zero ao Lucro](https://ggmax.com.br/anuncio/do-zero-ao-lucro-na-ggmax-guia-pratico-para-iniciantes); [GGMAX - Ebook](https://ggmax.com.br/anuncio/ebook-ggmax-otimize-seus-anuncios-ggmax-e-venda-mais); [GGMAX - Destaque seu anúncio](https://ggmax.com.br/anuncio/destaque-seu-anuncio-e-venda-muito-mais-rapido-kxg0k7uw)
- Compras abaixo de R$ 25 pagam uma "Taxa Operacional", cobrada do comprador no momento da transação, e a plataforma pode alterá-la a qualquer momento. — [Termos de uso - GGMAX](https://www.ggmax.com.br/termos-de-uso)

**GGMax: pós-compra**
- A garantia só vale se o pedido de intervenção for aberto dentro do prazo exibido **no chat da compra**. O pedido passa por análise da moderação e não é automático. — [FAQ - GGMAX](https://ggmax.com.br/faq); [TechTudo, jun/2024](https://www.techtudo.com.br/guia/2024/06/ggmax-e-seguro-conheca-o-site-de-compra-e-venda-de-jogos-skins-e-mais-edjogos.ghtml)
- Segundo a TechTudo (jun/2024), passado esse prazo o reembolso depende só do vendedor. — [TechTudo, jun/2024](https://www.techtudo.com.br/guia/2024/06/ggmax-e-seguro-conheca-o-site-de-compra-e-venda-de-jogos-skins-e-mais-edjogos.ghtml)
- Prazos de liberação ao vendedor: 4 dias para moedas virtuais, gold e itens, e 7 dias para contas, powerlevel e serviços. A "Liberação Acelerada" corta o prazo pela metade se o comprador marcar o pedido como entregue e avaliar o vendedor positivamente. — [Tarifas e prazos - GGMAX](https://ggmax.com.br/tarifas-e-prazos); [Quadro a Quadro - O que é Ggmax?](https://quadro-a-quadro.blog.br/o-que-e-ggmax/)
- O FAQ avisa que negociar fora da plataforma pode resultar em chargeback e perda do produto ou do dinheiro. — [FAQ - GGMAX](https://ggmax.com.br/faq)

**GGMax: mobile e apps**
- A busca por app do GGMax nas lojas não achou listagem própria. O único resultado foi um app chamado "GG", sem relação, de rastreamento de jogos. — [App Store - GG (id1320588074)](https://apps.apple.com/app/id1320588074); [AlternativeTo - GG App](https://alternativeto.net/software/ggapp/about)
- Há conteúdo indexado no Kwai sobre o GGMAX que destaca contas compartilhadas da Steam "com entrega automática", o que sugere presença em vídeo curto (o autor do conteúdo não foi verificado). — [Kwai - GGMAX](https://www.kwai.com/discover/GGMAX-?lang=es)

**Referências de UX de concorrentes**
- Na Codashop, a compra de recarga dispensa login e cadastro. O fluxo é "insira seu ID do jogador, selecione, compre e finalize o pagamento", e os créditos são adicionados imediatamente. — [Codashop - Recarga Free Fire](https://app.codashop.com/pt-br/free-fire); [Codashop News BR - Como comprar diamantes](https://news.codashop.com/br/como-comprar-diamantes-de-free-fire-na-codashop-brasil/); [TechTudo, nov/2021](https://www.techtudo.com.br/noticias/2021/11/codashop-e-confiavel-site-faz-recarga-de-diamantes-no-free-fire.ghtml)
- Os meios de pagamento da Codashop BR incluem Pix, cartão, PicPay, Mercado Pago, boleto, PayPal e cobrança no saldo do celular (sem cartão nem conta bancária). — [Codashop - Recarga Free Fire](https://app.codashop.com/pt-br/free-fire); [Codashop News BR - saldo de celular](https://news.codashop.com/br/how-to-buy-free-fire-diamonds-on-codashop-brazil-using-mobile-credit/); [Codashop News BR - PayPal](https://news.codashop.com/br/top-up-ff-paypal/); [Codashop News BR - PicPay](https://news.codashop.com/br/top-up-ff-picpay/)
- A Codashop oferece cadastro opcional, com o incentivo de dar "acesso a eventos e ofertas exclusivas". — [Codashop - Recarga Free Fire](https://app.codashop.com/pt-br/free-fire)
- Na G2G, o rótulo de entrega instantânea vale por anúncio: alguns gift cards são entregues na hora, outros podem levar algumas horas. — [G2G - Valorant Points](https://www.g2g.com/categories/valorant-gift-cards)
- O pós-compra da Eldorado.gg dá ao comprador 3 dias para revisar e marcar o pedido como recebido. Sem ação, o pedido é marcado como recebido automaticamente. — [Eldorado Support - TradeShield (Buying)](https://support.eldorado.gg/en/articles/8408994-tradeshield-buying)
- Na PlayerAuctions, o comprador tem no máximo 72 horas para aceitar ou abrir disputa no pedido. — [PlayerAuctions Support - After-sale protection](https://support.playerauctions.com/hc/en-us/articles/4402691743257-How-does-after-sale-protection-work)
- O app da G2G existe para iOS e Android. — [Google Play - G2G](https://play.google.com/store/apps/details?id=com.g2g.www&hl=en_SG); [MWM - G2G Shopping App](https://mwm.ai/apps/g2g/6443876260)
- O Rei dos Coins tem app Android do tipo "webview", ou seja, o site empacotado como app. — [Google Play - Rei dos Coins](https://play.google.com/store/apps/details?id=com.reidoscoins.webview&hl=en_US)

### Inferences
- **O que o GGMax faz bem:** oferta ampla e muita liquidez (ver tráfego na seção 4), anúncio gratuito, que atrai oferta, e ferramentas de automação para vendedor (estoque automático). O escrow também resolve a confiança básica entre estranhos.
- **O que o GGMax faz mal (do ponto de vista do comprador):** (a) a ordem da vitrine e da busca é parcialmente paga, e não por mérito ou preço; (b) a garantia e o prazo ficam "escondidos" no chat do pedido, e não na página do produto; (c) há uma taxa extra em pedidos pequenos; (d) categorias fora do tema (cursos, sites, "como vender no GGMax") diluem a experiência gamer; (e) não há app próprio identificado. Os itens (a) a (d) se apoiam nas fontes acima. O (e) depende de uma busca que não encontrou app e deve ser verificado manualmente.
- Uma loja de vendedor único não precisa de chat de negociação, ranking de vendedores nem destaque pago. Pode adotar uma UX de catálogo/e-commerce, com página de produto padronizada, preço final e prazo visíveis, e checkout curto. Para recargas e gift cards, o fluxo Codashop (ID do jogador e Pix, sem cadastro) é a referência de menor atrito.
- Para mobile, um PWA ou site responsivo é suficiente no lançamento. Os concorrentes BR menores usam app "webview" (Rei dos Coins), e o próprio GGMax não tem app identificado.

### Gaps
- Não foi possível percorrer de fato a home, os filtros, a página de anúncio, o checkout e a página de pedido do GGMax e dos concorrentes, porque o WebFetch falhou por DNS. Faltam detalhes como os filtros disponíveis, a presença de capturas de tela da conta, os campos da ficha da conta, a exigência de login antes do checkout e o rastreio do pedido.
- A existência de app ou PWA do GGMax não foi confirmada nas lojas (a busca só achou um app "GG" sem relação).
- Não foram levantados dados de UX de FunPay, Kinguin e Eneba além do que aparece nas seções 2 e 3.

## 2. Funcionalidades de confiança e conversão (garantias, selos, verificação, avaliações, rastreio, entrega instantânea, chat, FAQ, prova social)

### Takeaway
Todos os líderes usam escrow e janelas de garantia por categoria. Os globais transformaram a garantia em **produto**: garantia estendida paga de 3 ou 6 meses na Eldorado, "seguro" contra recuperação da conta pelo dono original na PlayerAuctions e Buyer Protection paga na Kinguin. No GGMax, a garantia descrita nas fontes depende de abrir intervenção dentro do prazo mostrado no chat. Os sinais de confiança mais usados nos títulos das páginas são "Secure", "Verified" e "Largest". O Rei dos Coins aposta em identidade empresarial (CNPJ e sede física).

### Cited Findings
- **GGMax:** pagamento retido até a confirmação. A garantia depende de intervenção dentro do prazo exibido no chat, com análise da moderação. — [FAQ - GGMAX](https://ggmax.com.br/faq); [Como funciona - GGMAX](https://ggmax.com.br/como-funciona)
- **Eldorado.gg TradeShield:** o pagamento fica retido pela Eldorado até a conclusão do pedido. A garantia varia por categoria: contas têm 5 dias por padrão, contas de Fortnite 10 dias, contas de GTA 5 14 dias e gift cards 4 dias. Abrir disputa congela o pagamento. — [Eldorado Support - TradeShield (Buying)](https://support.eldorado.gg/en/articles/8408994-tradeshield-buying); [Eldorado Support - TradeShield (Selling)](https://support.eldorado.gg/en/articles/8409006-tradeshield-selling)
- **Eldorado.gg, garantia estendida:** no checkout, o comprador pode pagar para estender a garantia da conta para 3 ou 6 meses. Reembolsos válidos vão para o saldo Eldorado. — [Eldorado Support - Extended account warranty](https://support.eldorado.gg/en/articles/8408988-extended-account-warranty)
- **Eldorado.gg, limite:** se a publisher banir a conta depois da janela de garantia, a TradeShield não reembolsa. — [Eldorado Support - TradeShield (Buying)](https://support.eldorado.gg/en/articles/8408994-tradeshield-buying)
- **PlayerAuctions PlayerGuardian:** verificação de identidade dos usuários, retenção do pagamento até a confirmação da entrega e monitoramento de fraude. — [PA Blog - How PlayerAuctions Protects You from Scams](https://blog.playerauctions.com/about/playerauctions-scam-free/)
- **PlayerAuctions, contas:** oferece pacotes de "insurance" para reembolsar o comprador se o dono original recuperar a conta. — [PlayerAuctions - Safe Account Trading](https://www.playerauctions.com/about/safe-account-trade/)
- **PlayerAuctions, after-sale protection:** o vendedor pode oferecer 7, 14 ou 30 dias de proteção. Se o comprador perder o acesso e a conta não puder ser recuperada, recebe reembolso integral. A proteção da plataforma reembolsa só o valor coberto, não a taxa de proteção, e expira se o comprador revender a conta. — [PlayerAuctions Support - After-sale protection](https://support.playerauctions.com/hc/en-us/articles/4402691743257-How-does-after-sale-protection-work)
- **G2G, verificação de vendedor:** exige documento com foto (passaporte, CNH ou RG) e verificação do celular. — [G2G Support - How Do I Register as a Seller?](https://support.g2g.com/support/solutions/articles/5000556835-how-do-i-register-as-a-seller-)
- **G2G, ranks de vendedor:** há ranks de vendedor (de Normal a Legendary) por volume mensal de vendas e uma página de "store info". O detalhe de Legendary ≥ US$ 20 mil/mês veio do resumo de busca e não foi conferido na página. — [G2G Support - Seller Rank, Store Info and Commission](https://support.g2g.com/support/solutions/articles/5000001417-how-does-g2g-s-seller-rank-store-info-and-commission-system-work-to-your-advantage-)
- **G2G, outros sinais:** existe programa "GamerProtect" para vendedores (só o título foi visto). — [G2G Support - GamerProtect for Sellers](https://support.g2g.com/support/solutions/articles/5000804162-gamerprotect-for-sellers)
- **G2G, títulos de página:** usam palavras de confiança, como "Valorant Points For Sale - G2G Secure Marketplace", "Buy Apex Legends Gift Card on G2G.com - Secure & Verified" e "Buy Google Accounts - Verified Sellers on G2G". — [G2G - Valorant Points](https://www.g2g.com/categories/valorant-gift-cards); [G2G - Apex Legends Gift Card](https://www.g2g.com/categories/apex-legends-gift-cards); [G2G - Google Accounts](https://www.g2g.com/categories/google-accounts)
- **Kinguin Buyer Protection:** reviews de terceiros a descrevem como um adicional opcional e pago (uma delas fala em cerca de 10% do valor do código), com mediação, troca de chave ou reembolso, atendimento prioritário 24/7 e garantia de devolução em 30 dias. Os detalhes variam entre as fontes, e nenhuma página oficial foi lida. — [Digital Citizen - Is Kinguin legit](https://www.digitalcitizen.life/is-kinguin-legit-should-you-buy-keys/); [SecureBlitz - Kinguin Review](https://secureblitz.com/kinguin-review-safe-legit-or-scam/); [Prima Games - Is Kinguin safe](https://primagames.com/featured/is-kinguin-a-safe-and-legit-site-for-game-codes-answered)
- **FunPay:** chat direto entre comprador e vendedor, escrow até a confirmação da entrega e pagamentos por cartão, PayPal, Apple/Google Pay e cripto (segundo reviews de terceiros). A nota no Trustpilot é cerca de 4,3/5. — [Trustpilot - FunPay](https://www.trustpilot.com/review/funpay.com?page=2); [LegitBoosting - Is FunPay legit](https://legitboosting.net/is-funpay-legit/); [Tested.gg - FunPay](https://tested.gg/site/funpay)
- **FunPay, ranking:** a FunPay não publica as regras de ranking em detalhe. Na prática, velocidade de resposta e volume de negócios fechados parecem pesar. — [Foxreload - FunPay shop setup 2026](https://foxreload.com/en/library/marketplaces/funpay-open-shop-setup)
- **Rei dos Coins:** loja brasileira fundada em 2015 que exibe CNPJ e "sede física em São José, Santa Catarina". Declara que "não compramos nem vendemos contas de qualquer jogo", e a página "Quem Somos" conta a história "Do Tibia ao Nº1 em Gift Cards". — [Rei dos Coins - FAQ](https://www.reidoscoins.com.br/FAQ); [Rei dos Coins - Quem Somos](https://www.reidoscoins.com.br/Quem-Somos)
- **Rei dos Coins, redes sociais:** publica alertas sobre "PERFIS FALSOS se passando por nossa equipe". — [Facebook - Rei dos Coins](https://www.facebook.com/ReidosCoins/?locale=pt_BR)
- **Eldorado.gg, posicionamento:** a página "about us" usa o título "Largest In-Game Items Marketplace". — [Eldorado - About us](https://www.eldorado.gg/about-us)

### Inferences
- A garantia virou atributo comercial e fonte de receita nos líderes globais (extensão paga na Eldorado, insurance na PA, Buyer Protection na Kinguin). Nas fontes encontradas, o GGMax não tem garantia estendida ou seguro de conta. Isso é uma oportunidade clara de diferenciação, sujeito a confirmação no site.
- Um vendedor único controla o próprio estoque e a própria reputação, então pode oferecer **garantia padrão longa, exibida na página do produto** (e não no chat) e bancada pela própria loja. Também pode vender extensão opcional no modelo Eldorado.
- Em loja de vendedor único, não há "vendedor verificado" para exibir. O equivalente é a **verificação da empresa**: CNPJ, endereço, rostos dos sócios e histórico (padrão Rei dos Coins), mais selos de avaliação externos.
- O alerta contra perfis falsos do Rei dos Coins indica que golpes de falsificação de marca atingem lojas gamer brasileiras. Canais oficiais verificados e listados no site viram um elemento de confiança.

### Gaps
- Não foi possível verificar na página quais selos de confiança aparecem na home e no anúncio do GGMax, se há rastreio de pedido "ao vivo", chat de suporte ao vivo nem SLA de atendimento.
- Não foram encontradas fontes oficiais da Kinguin sobre preço e escopo da Buyer Protection, nem sobre o tempo de resposta do suporte de qualquer player.
- Uma review de terceiros disse que a G2G cobra do comprador uma taxa de processamento no checkout, mas não foi possível identificar a fonte com precisão.

## 3. Funcionalidades de retenção e monetização (fidelidade, cashback, VIP, cupons, indicação, afiliados, assinaturas, wishlist, sorteios)

### Takeaway
O GGMax tem um programa de pontos próprio, o GG Points (R$ 1 = 1 ponto, validade de 6 meses, ganho também em eventos no Discord e com cupons). A monetização vem de planos de vendedor que vendem visibilidade e de uma taxa para pedidos pequenos. Fora do Brasil, os padrões de referência são o "dia de resgate" semanal da G2G (Points Day às terças), o cashback com carteira da Eneba e os afiliados de 2 a 5% (Eneba). Em recargas no Brasil, a guerra é de bônus no Pix: 10% na Codashop contra 20% na Recarga Jogo (out/2026).

### Cited Findings
**GGMax**
- GG Points: programa de recompensa ("Lealdade"). A compra converte R$ 1 em 1 GG Point. A opção "Plano Adicional" dá pontos extras. Quem vende com o "Plano MAX" recebe 50% dos pontos do anúncio após avaliação positiva. Também há pontos por cupons promocionais e eventos no Discord. — [GGMAX - Programa de recompensa](https://ggmax.com.br/programa-de-recompensa)
- Anúncios Ouro e Diamante dão mais GG Points ao comprador. — [Tarifas e prazos - GGMAX](https://ggmax.com.br/tarifas-e-prazos)
- Os pontos valem como forma de pagamento no checkout ("GG Points"), expiram em 6 meses a partir da liberação e são liberados junto com o saldo do vendedor, ou seja, dependem da avaliação do pedido. — [GGMAX - Programa de recompensa](https://ggmax.com.br/programa-de-recompensa)
- É proibido comercializar GG Points, e conta banida perde o saldo de pontos. — [Termos de uso - GGMAX](https://www.ggmax.com.br/termos-de-uso)
- O programa é ensinado em vídeo no YouTube ("Como ganhar e usar GG POINTS?") e tem página de descoberta no TikTok ("Como usar as GG Points da GGMAX"). — [YouTube - GG Points](https://www.youtube.com/watch?v=tKKUXTD3l_k); [TikTok Discover - GG Points](https://www.tiktok.com/discover/como-usar-as-gg-points-da-ggmax)
- A monetização inclui comissão por plano (9,99% a 12,99%), destaque pago e "Taxa Operacional" do comprador em pedidos abaixo de R$ 25. — [Termos de uso - GGMAX](https://www.ggmax.com.br/termos-de-uso); [Tarifas e prazos - GGMAX](https://ggmax.com.br/tarifas-e-prazos)
- O programa de afiliados ("Trabalhe Conosco - Afiliados") exige ser criador de conteúdo com canal no YouTube, Twitch, TikTok ou Instagram. A página não informa comissão. — [GGMAX - Afiliados](https://www.ggmax.com.br/formulario/trabalhe-conosco-afiliados)

**Globais**
- G2G, pontos: o app anuncia o "G2G Points Day" toda terça-feira, quando é possível resgatar até 50% dos pontos disponíveis. — [Google Play - G2G](https://play.google.com/store/apps/details?id=com.g2g.www&hl=en_SG)
- Eneba, cashback: vale em produtos selecionados com a etiqueta "CASHBACK" e exige clicar em "Claim" para cair na carteira. Os limites são 3 produtos por dia, a carteira não paga a compra que gera cashback, e o uso só começa a partir de saldo de 5 EUR, com teto de 10 EUR por pedido. — [Eneba - What is Cashback](https://www.eneba.com/support/article/what-is-cashback-on-eneba); [Eneba - Received cashback](https://www.eneba.com/support/article/received-cashback); [Eneba - Limitations](https://www.eneba.com/support/article/limitations-cashback); [Eneba - How to use cashback](https://www.eneba.com/us/support/article/how-to-use-cashback-funds)
- Eneba, afiliados: 2 a 5% de revenue share, com pagamento possível em saldo da carteira. — [Eneba Affiliate Program](https://www.eneba.com/become-affiliate)
- Eldorado, garantia estendida: a extensão paga (3 ou 6 meses) é uma linha de receita no checkout. — [Eldorado Support - Extended account warranty](https://support.eldorado.gg/en/articles/8408988-extended-account-warranty)
- PlayerAuctions, proteção: a "protection fee" não é reembolsada nas disputas. — [PlayerAuctions Support - After-sale protection](https://support.playerauctions.com/hc/en-us/articles/4402691743257-How-does-after-sale-protection-work)
- Kinguin, fidelidade: as fontes de terceiros são conflitantes. Uma fala em programa por níveis ("Kinguin Mafia", com descontos e cashback), outra em moeda "Krowns" e sistema de tickets/XP. Não há confirmação oficial. — [GoCDKeys - Kinguin reliable 2026](https://gocdkeys.com/blog/kinguin-reliable-analysis-real-reviews-2026); [SecureBlitz - Kinguin Review](https://secureblitz.com/kinguin-review-safe-legit-or-scam/)

**Recargas no Brasil (bônus e cupons)**
- Agregador de cupons (ago/2026): cita 10% em diamantes bônus no Free Fire via Pix na Codashop e cashback de até 10%. — [Cia dos Descontos - Codashop](https://www.ciadosdescontos.com/cupom/codashop)
- Comparativo de out/2026: Codashop com bônus de 10%, contra a Recarga Jogo com "bônus de 20% no Pix" (R$ 4,49 por 120 diamantes nesse comparativo). — [GameOverDrive - Recarga Free Fire barato Pix 2026](https://gameoverdrive.com.br/recarga-free-fire-barato-pix-2/)
- Cupons do Rei dos Coins aparecem em agregadores (set/2026), e há matéria destacando "recarga de diamantes no FF com BÔNUS". — [CupomOnline - Rei dos Coins](https://www.cupomonline.com.br/cupom-rei-dos-coins/); [The Radioativo - Rei dos Coins](https://theradioativo.com.br/jogos/rei-coins-confiavel/)

### Inferences
- O GG Points tem atritos que um concorrente pode explorar: os pontos só são liberados depois da avaliação e do prazo do vendedor, expiram em 6 meses e se perdem se a conta for banida. Um cashback **imediato**, que não expira rápido e pode ser usado na próxima compra, é uma diferença simples de comunicar.
- Rituais de resgate (Points Day semanal da G2G) e cashback com regras simples (Eneba) criam motivo recorrente de visita. Para uma loja pequena, um "dia do bônus" semanal no Pix é barato e fácil de divulgar em comunidade (Discord ou WhatsApp).
- Em recargas e gift cards, o mercado brasileiro compete por bônus no Pix (10% a 20%). Uma loja nova dificilmente vence só no preço. O diferencial tende a estar em garantia, atendimento e cashback, não em mais desconto.
- Afiliados com código de criador (2 a 5% na Eneba; formulário de criadores no GGMax) são a forma padrão de transformar influenciadores em canal pago por desempenho.
- Garantia estendida opcional (modelo Eldorado/PA) é ao mesmo tempo diferencial de confiança e receita adicional por pedido.

### Gaps
- Nenhuma fonte encontrada sobre níveis VIP, assinaturas, wishlist ou alerta de preço, nem sobre sorteios recorrentes nos players analisados.
- As regras do "Plano Adicional" do comprador e do "Plano MAX" do GGMax (preço, quanto de ponto extra) não foram detalhadas nos trechos. A regra de "compra mínima 300+ GG Points" aparece cortada.
- Não há confirmação oficial do programa de fidelidade da Kinguin. Uma review de terceiros diz que a Eldorado não tem programa de fidelidade e faz só campanhas sazonais, mas não foi possível identificar a URL exata.

## 4. Canais de crescimento e tráfego (Similarweb/Semrush, SEO, influenciadores, comunidades, anúncios pagos e políticas)

### Takeaway
GGMax, G2G e Eldorado têm tráfego da mesma ordem de grandeza segundo a Semrush (cerca de 14 a 22 milhões de visitas por mês), dominado por acesso **direto** (70 a 82%), com o Google orgânico bem atrás (5 a 19%). Isso indica marcas consolidadas e recompra. As palavras-chave principais do GGMax são variações da própria marca. Os canais visíveis são afiliados e criadores (YouTube, TikTok, Twitch, Kwai), eventos no Discord, SEO de cauda longa por jogo e meio de pagamento (Codashop) e conteúdo comparativo "X é confiável?" (Eneba Hub). A Similarweb mostra que a G2G tem só uma pequena fatia de busca paga.

### Cited Findings
**Tráfego (estimativas de terceiros; divergentes)**

| Site | Fonte / data | Visitas | Fontes de tráfego e outros dados |
|---|---|---|---|
| ggmax.com.br | Semrush, jul/2026 | 17,88M (jul), 13,53M (jun), 16,69M (mai) | #123 no Brasil; tráfego orgânico ~1,23M — [Semrush](https://www.semrush.com/website/ggmax.com.br/overview/) |
| ggmax.com.br | Semrush, snapshot set/2025 | 14,03M (ago/2025), −1,41% vs. jul | Sessão média 11:46; Direto 82,22%, google.com 5,42%; público no Brasil, EUA e Portugal — [Semrush TR](https://tr.semrush.com/website/ggmax.com.br/overview) |
| ggmax.com.br | Similarweb, ago/2026 | 4,9M (o resumo de busca indica total de 3 meses; muito abaixo da Semrush) | 97,74% do tráfego de palavra-chave é orgânico; top keywords de marca: "ggmax", "gg max", "gg" — [Similarweb](https://www.similarweb.com/website/ggmax.com.br/) |
| g2g.com | Semrush, ago/2026 | 20,37M (ago), 22,56M (jul), 21,95M (jun); −9,68% vs. jul | Sessão média 10:49; Direto 73,33%, google.com 18,89% — [Semrush](https://www.semrush.com/website/g2g.com/overview/) |
| g2g.com | Similarweb, jul/2026 | 7,5M (o resumo indica total de 3 meses); −7,72% vs. mês anterior | Direto 56,49% (desktop), seguido de busca orgânica e social orgânico; orgânico 95,09% e pago 4,91% do tráfego de busca; EUA 20,55%, Alemanha 7,54%, Indonésia 4,96% — [Similarweb](https://www.similarweb.com/website/g2g.com/) |
| eldorado.gg | Semrush, snapshot nov/2025 | 16,14M (out/2025), 13,88M (set), 14,24M (ago) | Sessão média 10:25; Direto 70,47%, google.com 15,72% — [Semrush](https://www.semrush.com/website/eldorado.gg/overview) |

- A lista de concorrentes do GGMax na Semrush (abr/2025) traz dfg.com.br, gameflip.com e reidoscoins.com.br, com a eldorado.gg aparecendo com 7,14M de visitas naquela data. — [Semrush JA - ggmax competitors](https://ja.semrush.com/website/ggmax.com.br/competitors); [Semrush - ggmax competitors](https://www.semrush.com/website/ggmax.com.br/competitors/)
- A lista de concorrentes da Eldorado na Semrush (out/2025) traz a g2g.com com 17,54M de visitas. — [Semrush - eldorado competitors](https://www.semrush.com/website/eldorado.gg/competitors/)
- A Similarweb tem páginas de comparação G2G vs. Overgear, IGV e Eldorado, o que define o conjunto competitivo global da G2G. — [Similarweb - overgear vs g2g](https://www.similarweb.com/website/overgear.com/vs/g2g.com/); [Similarweb - igv vs g2g](https://www.similarweb.com/website/igv.com/vs/g2g.com/); [Similarweb - eldorado vs g2g](https://www.similarweb.com/website/eldorado.gg/vs/g2g.com/)

**SEO e conteúdo**
- A Codashop mantém um blog BR com páginas por **jogo e meio de pagamento**, como "Recarregue Free Fire com PayPal", "com PicPay" e "usando saldo de celular". É SEO de cauda longa por intenção transacional. — [Codashop News BR - PayPal](https://news.codashop.com/br/top-up-ff-paypal/); [Codashop News BR - PicPay](https://news.codashop.com/br/top-up-ff-picpay/); [Codashop News BR - saldo de celular](https://news.codashop.com/br/how-to-buy-free-fire-diamonds-on-codashop-brazil-using-mobile-credit/)
- A Eneba publica conteúdo comparativo sobre concorrentes no "Eneba Hub", como "Is G2G Legit?" e "Is Eldorado.gg Legit?", para capturar buscas pela marca alheia. — [Eneba Hub - Is G2G legit](https://www.eneba.com/hub/play-to-earn/is-g2g-legit/); [Eneba Hub - Is Eldorado legit](https://www.eneba.com/hub/play-to-earn/is-eldorado-gg-legit/)
- A busca "GGMax é confiável" é atendida por terceiros: TechTudo (jun/2024), Recargify ("Análise Honesta 2026"), SiteConfiável e blogs. Ou seja, há demanda de busca sobre confiança que o próprio GGMax não captura sozinho. — [TechTudo, jun/2024](https://www.techtudo.com.br/guia/2024/06/ggmax-e-seguro-conheca-o-site-de-compra-e-venda-de-jogos-skins-e-mais-edjogos.ghtml); [Recargify - GG Max é confiável? 2026](https://recargify.com/analise/ggmax-com-br-e-confiavel); [SiteConfiável - ggmax.com.br](https://www.siteconfiavel.com.br/site/ggmax-com-br)
- As páginas de categoria por jogo da G2G trazem palavras de confiança no título ("Secure Marketplace", "Secure & Verified"). — [G2G - Valorant Points](https://www.g2g.com/categories/valorant-gift-cards); [G2G - Apex Legends](https://www.g2g.com/categories/apex-legends-gift-cards)
- O GGMax tem blog oficial com conteúdo de ajuda ao vendedor, como anúncios dinâmicos e estoque automático. — [Blog GGMAX](https://ggmax.com.br/blog/anuncios-dinamicos-e-estoque-automatico-como-configurar-meu-anuncio)
- Sites de cupom (CupomOnline, Cia dos Descontos e blogs de afiliados) listam cupons de Codashop e Rei dos Coins, o que funciona como canal de afiliação. — [CupomOnline - Rei dos Coins, set/2026](https://www.cupomonline.com.br/cupom-rei-dos-coins/); [Cia dos Descontos - Codashop, ago/2026](https://www.ciadosdescontos.com/cupom/codashop); [Thiago Rodrigo - cupom Codashop](https://thiagorodrigo.com.br/cupom-desconto-codashop/)

**Influenciadores, criadores e comunidades**
- O GGMax recruta afiliados entre criadores com canais no YouTube, Twitch, TikTok ou Instagram. — [GGMAX - Afiliados](https://www.ggmax.com.br/formulario/trabalhe-conosco-afiliados)
- O GGMax distribui GG Points em "eventos no Discord". — [GGMAX - Programa de recompensa](https://ggmax.com.br/programa-de-recompensa)
- Há vídeos e conteúdo do GGMax no YouTube, no TikTok e no Kwai. — [YouTube - GG Points](https://www.youtube.com/watch?v=tKKUXTD3l_k); [TikTok Discover](https://www.tiktok.com/discover/como-usar-as-gg-points-da-ggmax); [Kwai - GGMAX](https://www.kwai.com/discover/GGMAX-?lang=es)
- A Eneba mantém uma equipe dedicada de marketing de influenciadores (vagas de team lead, manager e specialist mobile) focada em YouTube, Twitch e TikTok. As vagas têm entre cerca de 225 e 1.000 dias e refletem a estratégia passada ou contínua. — [MeetFrank - Eneba Influencer Team Lead](https://meetfrank.com/jobs/eneba-games/influencers-marketing-team-lead); [Jobgether - Eneba Influencers Manager](https://jobgether.com/offer/69a13a137f0cfae7f11f441e-influencers-manager); [MeetFrank - Eneba Influencer Specialist Mobile](https://meetfrank.com/jobs/eneba-games/influencer-marketing-specialist-mobile)
- A Eneba vende "brand partnerships" integradas à experiência de compra, com cashback e recompensas para parceiros (conteúdo patrocinado pela própria Eneba). Cita 15 milhões de compradores (dado de 2023), e outras fontes da empresa citam 10M+ ou 20M+ usuários ativos. — [Yahoo Finance - Eneba brand partnerships](https://finance.yahoo.com/news/eneba-explains-brand-partnerships-digital-130000927.html); [Wikipedia - Eneba](https://en.wikipedia.org/wiki/Eneba_(platform))
- A TheGamer publicou "Buying In-Game Items Online: What Actually Protects Your Money", cuja URL inclui "eldorado-gg". Isso sugere conteúdo de marca ou patrocinado da Eldorado na imprensa gamer (inferido pela URL, conteúdo não lido). — [TheGamer](https://www.thegamer.com/buying-in-game-items-online-protect-your-money-eldorado-gg/)

**Anúncios pagos e políticas**
- **Google Ads, "Enabling dishonest behavior":** a política proíbe promover produtos ou serviços feitos para permitir comportamento desonesto. Violações não levam a suspensão imediata: há aviso com pelo menos 7 dias de antecedência. A busca **não** encontrou menção explícita a venda de contas de jogos nessa política. — [Google Ads Policy - Enabling dishonest behavior](https://support.google.com/adspolicy/answer/6016086?hl=en)
- **Google Ads, cripto e NFT:** a política permite anúncios de jogos NFT com compras de itens no jogo (roupas, armas, armaduras virtuais), mas proíbe jogos em que se aposta NFT para ganhar cripto ou NFT. — [Google Ads Policy - Cryptocurrencies](https://support.google.com/adspolicy/answer/13985443?hl=en-GB); [Decrypt](https://decrypt.co/155185/google-changes-policy-allow-nft-game-ads-some-limits)
- A Similarweb estima que só 4,91% do tráfego de busca da G2G vem de mídia paga. — [Similarweb - g2g.com](https://www.similarweb.com/website/g2g.com/)

### Inferences
- A fatia de 70 a 82% de tráfego direto nos três grandes indica que o jogo é de **marca e recompra**, não de SEO. Uma loja nova precisa de canais que gerem lembrança de marca: criadores, comunidade e boca a boca. Depender de busca de marca alheia não basta.
- Como as palavras-chave principais do GGMax são de marca, é difícil competir de frente por "ggmax". A estratégia viável é cauda longa transacional, com uma página por jogo, por produto e por meio de pagamento (modelo Codashop), mais conteúdo de confiança e comparativo (modelo Eneba Hub), por exemplo "como comprar conta de [jogo] com segurança" e "garantia de conta: como funciona".
- A mídia paga é marginal para a G2G (4,91% da busca). Somada à política de "dishonest behavior" do Google, isso sugere que anúncios diretos de **venda de contas** são arriscados. Uma alternativa legítima comum é anunciar só produtos claramente permitidos (gift cards oficiais e recargas) e conteúdo institucional, e levar o tráfego de contas por canais orgânicos e criadores. Isso é inferência: não foi confirmado como os concorrentes fazem.
- Eventos no Discord (GGMax) e afiliados criadores (GGMax e Eneba) são canais baratos e replicáveis por uma loja de dois sócios.

### Gaps
- **Políticas de anúncios da Meta** sobre venda de contas e itens digitais de jogos não foram pesquisadas (o orçamento de buscas acabou). É preciso consultar as Meta Advertising Standards e as Commerce Policies.
- Não foi encontrada menção explícita de contas de jogos nas políticas do Google Ads. A política de Shopping e Merchant Center também não foi verificada.
- Faltam dados de tráfego (Similarweb/Semrush) de PlayerAuctions, FunPay, Eneba, Kinguin, Codashop, DFG e Rei dos Coins. A estimativa de cerca de 29,6M de visitas/mês para a FunPay apareceu numa review de terceiros não identificável com precisão e não foi verificada.
- Faltam a lista completa de palavras-chave e a divisão de tráfego social por rede (YouTube, TikTok, Discord, Instagram) para o GGMax.
- Faltam campanhas específicas de influenciadores do GGMax (nomes de criadores, cupons, valores) e o tamanho do Discord oficial.
- A grande divergência entre Semrush (cerca de 14 a 18M/mês) e Similarweb (4,9M em 3 meses, segundo o resumo) para o GGMax não pôde ser resolvida sem abrir as páginas.

## 5. Marca e comunidade (posicionamento, tom de voz, eventos, patrocínios de e-sports)

### Takeaway
O posicionamento dominante é **segurança e intermediação**: GGMax "com segurança", G2G "Secure & Verified" e Eldorado "o que realmente protege seu dinheiro". A Eldorado também se coloca como "maior" ("Largest In-Game Items Marketplace"). No Brasil, o Rei dos Coins usa história de origem (Tibia) e transparência empresarial (CNPJ e sede). A comunidade do GGMax gira em torno de Discord e pontos. Não foram encontradas fontes sobre patrocínio de e-sports.

### Cited Findings
- A cobertura do GGMax na imprensa o descreve como "o marketplace que promove a compra e venda de ativos digitais com segurança". — [Observatório Tech](https://observatoriotech.com.br/noticia/conheca-a-ggmax-o-marketplace-que-promove-a-compra-e-venda-de-ativos-digitais-com-seguranca/)
- O GGMax se descreve como plataforma em que o comprador recebe o produto ou serviço e o vendedor recebe o pagamento, com o GGMax como intermediador. — [GGMAX - Afiliados](https://www.ggmax.com.br/formulario/trabalhe-conosco-afiliados); [Como funciona - GGMAX](https://ggmax.com.br/como-funciona)
- O GGMax usa ranks de plano com nomes de metal e gema (Prata, Ouro, Diamante), linguagem de "ranqueadas" familiar a jogadores. — [Tarifas e prazos - GGMAX](https://ggmax.com.br/tarifas-e-prazos)
- O GGMax faz eventos de comunidade no Discord com premiação em GG Points. — [GGMAX - Programa de recompensa](https://ggmax.com.br/programa-de-recompensa)
- A Eldorado.gg se posiciona como "Largest In-Game Items Marketplace". — [Eldorado - About us](https://www.eldorado.gg/about-us)
- A G2G usa "Secure", "Verified" e "Verified Sellers" nos títulos das páginas de categoria. — [G2G - Apex Legends](https://www.g2g.com/categories/apex-legends-gift-cards); [G2G - Google Accounts](https://www.g2g.com/categories/google-accounts)
- O Rei dos Coins conta a narrativa "Do Tibia ao Nº1 em Gift Cards", destaca CNPJ e sede física e se distancia da venda de contas ("não compramos nem vendemos contas"). — [Rei dos Coins - Quem Somos](https://www.reidoscoins.com.br/Quem-Somos); [Rei dos Coins - FAQ](https://www.reidoscoins.com.br/FAQ)
- A Codashop destaca simplicidade ("Sem necessidade de login ou cadastro!"). — [Codashop News BR](https://news.codashop.com/br/como-comprar-diamantes-de-free-fire-na-codashop-brasil/)
- A Eneba se posiciona como "digital entertainment marketplace" e vende parcerias de marca. — [Yahoo Finance - Eneba](https://finance.yahoo.com/news/eneba-explains-brand-partnerships-digital-130000927.html)

### Inferences
- Como todos dizem "seguro", a palavra perdeu força como diferencial. Uma loja nova se destaca com **promessas verificáveis e específicas**, por exemplo "garantia de X dias escrita na página", "entrega em até N minutos ou cashback" ou "atendimento humano em até N minutos", e não com adjetivos.
- A narrativa de fundadores e identidade empresarial (Rei dos Coins) combina com uma loja de dois sócios. Rostos reais, CNPJ e história gamer são ativos de marca que um marketplace grande e impessoal não tem.
- Usar a linguagem dos jogadores (ranks, eventos no Discord) é padrão no segmento e deve ser mantido.

### Gaps
- Não foram encontradas fontes sobre patrocínios de e-sports ou times por GGMax, G2G, Eldorado, Eneba ou Kinguin (orçamento de buscas esgotado).
- Não foi possível analisar o tom de voz nas redes (Instagram, TikTok, X) dos players por falta de acesso às páginas.

## 6. Lacunas no mercado brasileiro e diferenciais concretos para uma loja de vendedor único

### Takeaway
Com base nas fontes, as maiores brechas do GGMax para o comprador são: garantia condicionada ao prazo do chat e à moderação, sem garantia estendida ou seguro; prazos de 4 a 7 dias pensados para o vendedor; taxa operacional em pedidos abaixo de R$ 25; vitrine e busca com destaque pago; pontos que expiram em 6 meses e dependem da avaliação; e catálogo disperso. Uma loja de vendedor único pode atacar exatamente esses pontos, combinando com padrões globais comprovados: garantia estendida (Eldorado), seguro contra recuperação da conta (PlayerAuctions), checkout sem login com Pix (Codashop), cashback ou dia de resgate (Eneba/G2G) e transparência empresarial (Rei dos Coins).

### Cited Findings
- No GGMax, a garantia exige intervenção dentro do prazo do chat e passa por moderação. Depois do prazo, o reembolso depende do vendedor (TechTudo, jun/2024). — [FAQ - GGMAX](https://ggmax.com.br/faq); [TechTudo, jun/2024](https://www.techtudo.com.br/guia/2024/06/ggmax-e-seguro-conheca-o-site-de-compra-e-venda-de-jogos-skins-e-mais-edjogos.ghtml)
- Os prazos de liberação do GGMax são de 4 dias para itens e moedas e 7 dias para contas e serviços. — [Tarifas e prazos - GGMAX](https://ggmax.com.br/tarifas-e-prazos)
- O GGMax cobra taxa operacional do comprador em compras abaixo de R$ 25. — [Termos de uso - GGMAX](https://www.ggmax.com.br/termos-de-uso)
- No GGMax, o destaque na home e na busca é vendido por plano. — [Tarifas e prazos - GGMAX](https://ggmax.com.br/tarifas-e-prazos)
- Os GG Points expiram em 6 meses e são liberados junto com o saldo do vendedor. — [GGMAX - Programa de recompensa](https://ggmax.com.br/programa-de-recompensa)
- A Eldorado vende garantia estendida de conta (3 ou 6 meses) no checkout. — [Eldorado Support - Extended account warranty](https://support.eldorado.gg/en/articles/8408988-extended-account-warranty)
- A PlayerAuctions oferece "insurance" contra recuperação da conta pelo dono original e proteção pós-venda de 7, 14 ou 30 dias. — [PlayerAuctions - Safe Account Trading](https://www.playerauctions.com/about/safe-account-trade/); [PlayerAuctions Support](https://support.playerauctions.com/hc/en-us/articles/4402691743257-How-does-after-sale-protection-work)
- A Codashop permite compra sem login, credita na hora e aceita Pix, PicPay, Mercado Pago, boleto e saldo de celular. — [Codashop - Recarga Free Fire](https://app.codashop.com/pt-br/free-fire); [Codashop News BR - saldo de celular](https://news.codashop.com/br/how-to-buy-free-fire-diamonds-on-codashop-brazil-using-mobile-credit/)
- A Eneba devolve cashback na carteira. A G2G faz o Points Day semanal, às terças, com resgate de até 50% dos pontos. — [Eneba - What is Cashback](https://www.eneba.com/support/article/what-is-cashback-on-eneba); [Google Play - G2G](https://play.google.com/store/apps/details?id=com.g2g.www&hl=en_SG)
- Segundo reviews de terceiros, a Kinguin oferece atendimento prioritário 24/7 e devolução em 30 dias para quem compra a Buyer Protection. — [SecureBlitz - Kinguin Review](https://secureblitz.com/kinguin-review-safe-legit-or-scam/); [Digital Citizen - Kinguin](https://www.digitalcitizen.life/is-kinguin-legit-should-you-buy-keys/)
- O Rei dos Coins exibe CNPJ e sede física e alerta contra perfis falsos. — [Rei dos Coins - FAQ](https://www.reidoscoins.com.br/FAQ); [Facebook - Rei dos Coins](https://www.facebook.com/ReidosCoins/?locale=pt_BR)
- Em recargas no Brasil, os bônus no Pix chegam a 20% (Recarga Jogo, out/2026). — [GameOverDrive, out/2026](https://gameoverdrive.com.br/recarga-free-fire-barato-pix-2/)
- A busca "GGMax é confiável" é dominada por terceiros (TechTudo, Recargify, SiteConfiável). — [Recargify 2026](https://recargify.com/analise/ggmax-com-br-e-confiavel); [SiteConfiável](https://www.siteconfiavel.com.br/site/ggmax-com-br)

### Inferences
**Lista curta de diferenciais propostos (todos inferidos a partir das fontes acima):**
1. **Garantia padrão longa, escrita na página do produto e bancada pela loja.** Por exemplo, 30 dias para contas, com reembolso por Pix, em vez de prazo escondido no chat. Como a loja é a própria vendedora, não precisa reter dinheiro de terceiros por 4 a 7 dias e pode prometer reembolso rápido.
2. **Garantia estendida ou "seguro de conta" opcional**, de 3 a 6 meses, cobrindo recuperação pelo dono original (modelos Eldorado e PlayerAuctions). É um diferencial que não aparece no GGMax pelas fontes e ainda gera receita.
3. **Preço final transparente.** Nada de "taxa operacional" em pedido pequeno, com o valor fechado desde a listagem. A comunicação pode ser "o preço que você vê é o que você paga", em contraste direto com a taxa do GGMax abaixo de R$ 25.
4. **Vitrine curada por mérito, não por destaque pago.** Poucos jogos, com profundidade: uma landing por jogo, com guia, FAQ e prazos. Evitar categorias fora do tema (cursos, serviços de site).
5. **Ficha técnica padronizada da conta**, com dados como data de criação, e-mail original incluso, inventário e capturas próprias, todos verificados pela loja. Um vendedor único consegue padronizar o que um marketplace C2C não consegue. Os aspectos de segurança da transferência ficam com outro pesquisador.
6. **Entrega instantânea real para estoque próprio**, com SLA exibido (por exemplo "entrega em até X min ou cashback") e status do pedido em etapas (pago, em entrega, entregue, garantia ativa até a data D).
7. **Checkout sem cadastro para recargas e gift cards** (padrão Codashop), com Pix e conta opcional que dá cashback.
8. **Cashback simples e imediato**, com validade longa, mais um "dia do bônus" semanal (inspirado no Points Day da G2G). Combate os pontos do GGMax, que expiram em 6 meses e só são liberados após avaliação.
9. **Atendimento humano com SLA publicado**, de preferência 24/7, ao menos por WhatsApp e Discord, como promessa pública. Benchmark: atendimento prioritário 24/7 da Buyer Protection da Kinguin.
10. **Transparência empresarial**: CNPJ, endereço, rostos e história dos sócios, e canais oficiais verificados listados no site, contra os golpes de perfis falsos.
11. **Conteúdo de confiança e comparativo em português** (modelo Eneba Hub e Codashop News), por exemplo "como comprar conta de [jogo] com segurança", "garantia de conta explicada" e "recarga [jogo] com Pix". Serve para capturar a demanda por "é confiável?".
12. **Programa de afiliados e criadores** com código e cashback para o seguidor (2 a 5% é a referência da Eneba), mais eventos no Discord. Mídia paga só para produtos claramente permitidos (gift cards e recargas), dado o risco com a política de "dishonest behavior" do Google.

**Riscos e contrapontos:**
- Um vendedor único **não tem a liquidez** (variedade de ofertas) do GGMax, que tem cerca de 14 a 18M de visitas por mês segundo a Semrush. Por isso, a proposta precisa ser "menos opções, mais garantia" e focar em poucos jogos.
- Bancar garantia longa exige provisão financeira e boa avaliação de risco de recuperação de conta. Isso deve ser cruzado com a pesquisa de segurança.

### Gaps
- Não foram encontradas fontes sobre SLA de atendimento, existência de chat ao vivo 24/7 ou "reembolso instantâneo" no GGMax ou em concorrentes brasileiros. A afirmação de que esses recursos "faltam no mercado brasileiro" não pôde ser confirmada com dados e precisa de verificação manual.
- Concorrentes brasileiros menores (DFG, lojas de contas de Free Fire, Roblox ou Valorant, Recarga Jogo e outros) não foram mapeados em profundidade.
- Faltam a confirmação de políticas da Meta e a forma como os concorrentes anunciam na prática (por exemplo, pela Biblioteca de Anúncios da Meta e pelo Centro de Transparência do Google Ads).
