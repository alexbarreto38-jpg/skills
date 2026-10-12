# Fornecimento de estoque e entrega automática para uma loja gamer de 2 sócios (Brasil, out/2026)

> **Nota metodológica (leia antes de usar):** nesta sessão o WebFetch falhou com erro de DNS em todos os domínios (inclusive ggmax.com.br, reloadly.com, ezpin.com e wikipedia.org). Por isso não li nenhuma página na íntegra. Todos os fatos abaixo vêm de **resumos de resultados do WebSearch**, e cada um traz a URL de origem. Depois de cerca de 19 buscas, o limite de buscas da sessão (compartilhado com outros agentes) se esgotou. Ficaram sem pesquisa: Ding, Wogi, Midasbuy/PUBG UC, Moonton/MLBB, Riot Points no varejo, verificação de contas e equipe de boosting. Tudo isso aparece como lacuna. Datas: quando a fonte indica o ano, ele vem entre parênteses. Sem data, trate a informação como "não datada" e confirme com o fornecedor antes de decidir.

## 1. Fornecedores atacadistas/API de gift cards e keys utilizáveis a partir do Brasil (requisitos, preço, integração)

### Takeaway
Para gift cards em BRL (Xbox, PlayStation Store, Steam, Google Play, Apple, LoL), o caminho mais "limpo" para um CNPJ brasileiro pequeno são os **agregadores nacionais com API**: Celcoin, RV Hub/RV Digital e Hype Games (Level Up). Todos vendem PIN por API, mas nenhum publica tabela de desconto, e é preciso negociar. Os agregadores globais (Reloadly, EZ PIN, Bamboo) têm API pronta e cadastro rápido, mas não confirmei a cobertura de produtos BRL nem os requisitos de KYB para o Brasil. Kinguin, G2A e Eneba são **marketplaces de keys** com API de vendedor, não distribuidores oficiais: o estoque comprado ali é de origem mista (gray market).

### Cited Findings
**Agregadores/distribuidores brasileiros**
- A Celcoin oferece recargas de jogos e gift cards por API, com títulos como Xbox, PlayStation Store, League of Legends e Steam (página não datada) — [Celcoin – Recargas](https://www.celcoin.com.br/cel_payments/recargas/)
- A documentação da Celcoin separa a recarga de **PIN** (o código é entregue ao usuário para resgate) da recarga **online** (o crédito cai direto com os dados enviados na requisição). Jogos são a categoria 2 e conteúdo digital a categoria 5 — [Celcoin Developers – Sobre recargas nacionais](https://developers.celcoin.com.br/docs/sobre-recargas-nacionais)
- Para integrar com a Celcoin é preciso ter chave de API, usar OAuth 2.0 e ter o produto habilitado em produção. A API **não envia webhooks**, então o status tem de ser consultado por polling. Há também um arquivo de movimentação via SFTP com as recargas do dia anterior — [Celcoin Developers – Realizar uma recarga](https://developers.celcoin.com.br/docs/realizar-uma-recarga); [Celcoin Developers – Sobre recargas nacionais](https://developers.celcoin.com.br/docs/sobre-recargas-nacionais)
- A central de suporte da Celcoin tem um artigo sobre "recarga de conteúdo digital / gift card" — [Suporte Celcoin](https://suporte.celcoin.com.br/hc/pt-br/articles/11561023588123-O-que-%C3%A9-um-gift-card)
- O RV Hub (da RV Digital) tem uma API de recarga de PIN que vende gift cards e recarrega jogos e apps como Apple e Google Play. Diz ter mais de 500 parceiros, número que não verifiquei — [RV Hub](https://www.rvhub.com.br/); [RV Digital – LinkedIn](https://br.linkedin.com/company/rvdigitaloficial)
- A Hype Games é a plataforma de distribuição digital da Level Up. Vende gift cards, moeda virtual e créditos de jogos e passou de 100 parceiros ativos (set/2025). Os modelos B2B incluem integração por API para lojas e apps, white label, loja pronta e "soluções simplificadas para pequenos varejistas" — [JWave (set/2025)](https://www.jwave.com.br/2025/09/hype-games-ultrapassa-100-parceiros-e-mira-expansao-digital-no-brasil/); [Gamers & Games (23/09/2025)](https://www.gamersegames.com.br/2025/09/23/hype-games-ultrapassa-100-parceiros-e-acelera-expansao-digital-no-brasil/); [Level Up – Hype Games](https://br.leveluplatam.com/hypegames/)
- Entre os parceiros da Hype citados estão Kabum, Mercado Livre, Shopee, Livelo e Vivo Valoriza. Em 2021 a empresa lançou o "Hype BIZ", voltado a vender créditos para e-commerces. Um perfil de 2021 descreve a Level Up como a maior distribuidora digital de games do Brasil, com parceiros como Sony, Microsoft, Garena e Ubisoft — [Republica DG](https://republicadg.com.br/hype-games-amplia-catalogo-e-se-consolida-como-referencia-em-distribuicao-digital-no-brasil/); [GameVicio (nov/2021)](https://www.gamevicio.com/noticias/2021/11/conheca-o-hype-games-loja-que-reune-o-melhor-do-universo-de-jogos/); [Adrenaline – Kabum vende créditos Hype](https://www.adrenaline.com.br/games/kabum-agora-vende-jogos-e-creditos-da-hype-games-para-pc-e-consoles/)
- Não encontrei página pública de cadastro de revendedor, margens ou pedido mínimo da Hype Games — [Level Up – Hype Games](https://br.leveluplatam.com/hypegames/)
- No varejo, a Ponto (grupo Casas Bahia) aponta como administradora dos gift cards a **BlackHawk Network Brasil S.A., CNPJ 13.880.252/0001-02**. Isso indica que a Blackhawk faz a ponte com os donos de conteúdo no varejo brasileiro, mas não é um programa de revenda publicado — [Pontofrio – Gift Card](https://www.pontofrio.com.br/l/giftcard.aspx?nid=202501)

**Agregadores globais com API**
- **Reloadly:** o cadastro é gratuito. As credenciais (client_id/client_secret) ficam na área Developers e geram um token OAuth exigido em todas as chamadas. Dá para listar os gift cards disponíveis no Brasil pela API com o código ISO "BR". Um exemplo de pedido entrega o código no e-mail e no telefone do destinatário, e quem envia pode ser de outro país — [Reloadly – How to order a gift card](https://reloadly.com/blog/?p=2787); [Reloadly – Gift card reseller API](https://www.reloadly.com/blog/gift-card-reseller-api/)
- A Reloadly diz que empresas podem revender mais de 150 marcas de gift card em 25 países de 4 regiões. O material não diz se o Brasil é um desses países. O blog cita "descontos e comissões claramente definidos" e "sem necessidade de contrato" como vantagens, mas isso é marketing do próprio fornecedor — [Reloadly – Gift card reseller API](https://www.reloadly.com/blog/gift-card-reseller-api/)
- **EZ PIN:** fica em San Diego (EUA). A API v2 exige client ID + secret key, **whitelist de IP** e access token em todas as requisições. Tem sandbox, webhooks e um catálogo filtrável por categoria, moeda e mercado geográfico. Não achei nada sobre produtos da América Latina — [Crunchbase – EZ PIN](https://www.crunchbase.com/organization/ez-pin); [EZ PIN – API v2.0](https://ezpin.com/blog/ez-pin-api-version-2-0-announced-complete-guide/); [EZ PIN – Business Solutions 2026](https://ezpin.com/blog/ez-pin-business-solutions-everything-you-need-to-know/)
- **Bamboo Card:** funciona por portal, API ou integração embarcada e afirma que "a maioria dos parceiros entra no ar em dias". Tem sandbox. Segundo o FAQ da API, a cobrança só ocorre **depois que o gift card é entregue com sucesso** ao usuário final. Existe um pacote Laravel da comunidade com URLs separadas de sandbox e produção (cerca de 635 dias atrás, ou seja, ~2025) — [Bamboo Card](https://www.bamboo-card.com/); [Bamboo API](https://new.bamboo-card.com/bamboo-api/); [GitHub – bamboo-card-portal](https://github.com/vahidkaargar/bamboo-card-portal)
- **Razer Gold (distribuição):** o hub de distribuição pede **empresa registrada no seu país e canal de vendas próprio** (site, rede de negócios etc.) e oferece um sistema de pedidos self-service (OMS) com e-PINs. A página de parceiros lista o Brasil entre os mercados — [Razer Gold Distribution Hub](https://distribution.gold.razer.com/); [Grow with Razer Gold](https://partners.gold.razer.com/)
- Um tópico da comunidade Razer indica o formulário https://developer.razer.com/contact/ para quem quer ser parceiro. Uma listagem de terceiros diz que a Razer procura distribuidores na América Latina e Caribe, mas a fonte não é oficial — [Razer Insider – distribuidor de pines](https://insider.razer.com/razer-gold-silver-20/distribuidor-de-pines-razer-gold-27887); [Elioplus – Razer](https://elioplus.com/profiles/vendors/31682/razer)
- Algumas lojas se dizem distribuidoras autorizadas de Razer Gold BR, como a TOPUPLive. Isso é autodeclaração — [TopUpLive – Razer Gold Brazil](https://www.topuplive.com/razer-gold-brazil/); [MooGold – Razer Gold Brazil](https://moogold.com/product/razer-gold-brazil-brl/)
- Como referência de processo, o onboarding da Amazon Incentives API (gift cards Amazon) segue estas etapas: conta corporativa → portal → integração da API → **financiar a conta (pré-pago)** → lançamento. A configuração manual leva 1–2 dias úteis — [Amazon Developer – Onboarding Process](https://developer.amazon.com/docs/incentives-api/onboarding-process.html)

**Marketplaces de keys com API (não são distribuidores oficiais)**
- **Kinguin:** a API de vendedor exige conta na Kinguin. O acesso é pedido por mensagem, informando ambiente (produção/sandbox), e-mail, nome da aplicação e se usará "declared stock". O sandbox roda no mesmo domínio da produção, então pode haver conflito de cookies — [Kinguin Seller Hub – Sellers API](https://kinguin-seller-hub.document360.io/docs/publicapidocumentationv2)
- O plugin "Kinguin API for WooCommerce" no WordPress.org está sem atualização há mais de 2 anos, e há avaliações dizendo que a entrega de keys não funciona — [WordPress.org – Kinguin plugin](https://en-za.wordpress.org/plugins/kinguin/)
- Não achei nenhum programa chamado "Kinguin for Business" nas buscas (lacuna).
- **G2A:** a própria G2A diz que não guarda nem vende keys, que a maioria das keys vem de "atacadistas verificados como empresa" e que todos os vendedores são empresas verificadas. A verificação pode pedir prova da origem das keys — [G2A – What is the source of the keys](https://supporthub.g2a.com/marketplace/en/G2A-Services/what-is-the-source-of-the-keys-on-g2a); [G2A – How we operate](https://www.g2a.co/security/how-we-operate/)
- O acesso à API da G2A não exige já comprar ou vender na plataforma. As credenciais (Client ID/Secret) ficam em Account settings → Store settings → API integration, segundo um guia de terceiro — [G2A – Import API Integration Q&A](https://supporthub.g2a.com/seller/en/g2a-api/import-api-integration-qa); [Keysender – Integrating G2A](https://support.keysender.com/article/integrating-g2a)
- **Eneba:** a API é GraphQL com OAuth 2.0 e serve só a comerciantes da Eneba. A documentação lista operações de "wholesale" (comprar leilões wholesale, exportar catálogo wholesale) e de "Declared Stock". Já o suporte diz que a Eneba **não oferece opção de atacado**, que as keys da plataforma "não se destinam à revenda" e que só pode vender quem compra de distribuidores oficiais. As fontes se contradizem — [Eneba API docs](https://api.eneba.com/documentation/); [Eneba – Wholesale option](https://www.eneba.com/support/article/wholesale-option); [Eneba – Can I buy from other vendors and resell](https://www.eneba.com/support/article/can-buy-other-vendors-resell)
- Atacadistas B2B como FazerCards, FoxReload e wholesaledigitalkey.com anunciam APIs REST para revenda automatizada. São páginas promocionais, sem verificação independente da origem do estoque — [FazerCards vs G2A](https://reseller.fazercards.com/en/compare/fazercards-vs-g2a); [Wholesale Digital Key API](https://wholesaledigitalkey.com/api.html); [FoxReload – Sell game keys on Eneba](https://foxreload.com/en/library/marketplaces/sell-game-keys-eneba)
- Uma comparação de software descreve a "Yard" como API de atacado para bens digitais, com catálogo único, saldo único e mais de 5.000 SKUs. A fonte é fraca — [Slashdot – comparison](https://slashdot.org/software/comparison/GiftWise-vs-yard-api/)

### Inferences
- O modelo financeiro comum entre os agregadores é **saldo pré-pago (wallet)** + API com OAuth. A Bamboo cobra só após a entrega, e a Amazon pede "financiar a conta". Os sócios precisam prever capital de giro parado no saldo de cada fornecedor.
- Para cartões BRL das plataformas grandes (PSN, Xbox, Steam, Google Play), os candidatos mais naturais são Celcoin, RV Hub e Hype Games. Os três já atendem varejistas brasileiros e operam em reais, o que evita IOF/câmbio e o risco de região errada (inferência; não confirmei que aceitam um CNPJ pequeno nem os descontos).
- A Blackhawk Network Brasil é um contato possível, mas parece mirar grandes varejistas físicos e online (inferência pelo exemplo da Ponto).
- Kinguin, G2A e Eneba servem mais como **canal de venda** extra para a própria loja do que como fornecedores legítimos. Comprar ali para revender traz risco de origem (ver seção 3) e, no caso da Eneba, viola a regra da própria plataforma.

### Gaps
- **Ding, Wogi**, InComm Brasil e Epay/Euronet Brasil não foram pesquisados porque o limite de buscas acabou.
- Não achei requisitos formais (CNPJ, faturamento mínimo, depósito mínimo, KYB) de Celcoin, RV Hub, Hype Games, Reloadly, EZ PIN ou Bamboo para um revendedor brasileiro pequeno.
- Nenhuma fonte trouxe tabela de desconto por marca (PSN/Xbox/Steam BRL) de qualquer distribuidor.
- Leads que apareceram sem detalhes: [Portal dos Créditos – Revenda](https://www.portaldoscreditos.com.br/loja/revenda) e a lista comercial [Vivendo Marketing – 5 fornecedores de gift card](https://vivendomarketing.com/5-fornecedores-de-gift-card-confiaveis-para-revender/). Não deu para avaliar a idoneidade de nenhum dos dois.

## 2. Programas oficiais de revenda de top-up direto (Free Fire, Robux, Valorant, PUBG UC, MLBB, Genshin)

### Takeaway
Os publishers concentram o top-up direto em poucos parceiros oficiais: Codashop, Razer Gold e, no Brasil, Hype Games e o próprio Recarga Jogo da Garena. Uma empresa pequena consegue entrar **como revendedora desses agregadores** (programa de revenda Codashop, distribuição Razer Gold, B2B Hype Games/Celcoin), e não direto com o publisher. Sites como a LootBar se apoiam nesses canais, e o status "oficial" deles muitas vezes não está confirmado.

### Cited Findings
- **Free Fire / Garena:** o site oficial indicado pela Garena para jogadores brasileiros é o Recarga Jogo (recargajogo.com.br), criado em 2017 para vender moeda virtual (TechTudo, mai/2026) — [TechTudo (2026)](https://www.techtudo.com.br/guia/2026/05/como-recarregar-diamante-no-free-fire-descubra-a-maneira-mais-segura-edjogos.ghtml)
- O Recarga Jogo aceita Pix e boleto, dá bônus de 10% em diamantes e permite login só com o ID do jogador, sem senha (Bolavip, fev/2022). Segundo o TechTudo (2019), o boleto pode levar cerca de 3 dias úteis para compensar — [Bolavip (2022)](https://br.bolavip.com/games/Free-Fire-conheca-o-Recarga-Jogo-site-oficial-para-comprar-diamante-por-PIX-cartao-e-boleto--Games-20220222-0132.html); [TechTudo (2019)](https://www.techtudo.com.br/dicas-e-tutoriais/2019/06/o-site-recarga-jogo-e-confiavel-veja-como-funciona-com-free-fire.ghtml)
- Pelo menos uma fonte de 2026 cita Razer Gold e Hype Games como revendedores autorizados indicados para Free Fire. O resumo da busca não diz exatamente qual fonte; os candidatos são estes — [Celular.pro.br (2026)](https://celular.pro.br/recarga-jogo-free-fire/); [TechTudo (2026)](https://www.techtudo.com.br/guia/2026/05/como-recarregar-diamante-no-free-fire-descubra-a-maneira-mais-segura-edjogos.ghtml)
- A Codashop diz ser "parceira oficial da Garena" para diamantes Free Fire, e a página das Filipinas se chama "Official Distributor". Os rodapés têm os links "Become a distributor" e "For Publishers: Register your title" — [Codashop – Free Fire (UK)](https://www.codashop.com/en-gb/free-fire); [Codashop – Garena Free Fire PH](https://www.codashop.com/en-ph/garena-free-fire-ph)
- **Programa de Revenda Codashop:** o interessado preenche um formulário e o time de business development analisa. Duas versões da central de ajuda dão prazos diferentes de resposta, 2 dias úteis e 14 dias, e não está claro qual é a mais recente — [Codashop Reseller Program (global)](https://global.support.codashop.com/hc/en-us/articles/6097511814927-Codashop-Reseller-Program); [Codashop Reseller Program (EG)](https://eg.support.codashop.com/hc/en-us/articles/5868568156175-Codashop-Reseller-Program)
- A StartSelect (Europa) se apresenta como "Revendedor oficial da Garena Free Fire". A recarga é feita pelo ID do jogador ou por código, e o produto não aceita devolução nem reembolso — [StartSelect – Free Fire 1080 diamantes](https://startselect.com/pt-pt/free-fire-1080-diamonds/72119)
- **Genshin/HoYoverse:** segundo a StarDB (wiki de fãs que ganha comissão da LootBar, ou seja, fonte parcial), os parceiros oficiais de top-up de terceiros da miHoYo são **Codashop e Razer Gold**, e a LootBar usaria o canal da Razer Gold. A PC Tech Magazine (jun/2026) descreve a LootBar como plataforma de terceiros, **não** revendedora formal autorizada da HoYoverse — [StarDB – parceria LootBar](https://stardb.gg/en/posts/official-partnership-with-lootbar-for-top-ups); [PC Tech Magazine (jun/2026)](https://pctechmag.com/2026/06/lootbar-for-genshin-impact-an-honest-look-at-the-value-play/)
- A LootBar afirma que "muitos" top-ups vêm de colaborações oficiais com desenvolvedores e outros de "canais autorizados de top-up". O fluxo é escolher o jogo e o pacote, informar UID e servidor e pagar. A conclusão costuma levar 3–5 minutos, sem pedir senha — [LootBar – blog](https://lootbar.gg/blog/en/lootbar-top-up-cheap-fast-safe.html); [LootBar – Top Up](https://www.lootbar.com/top-up/)
- **Roblox:** pelos termos (versão de Singapura), gift cards devem ser comprados em varejistas e distribuidores autorizados ou em roblox.com/giftcards. Cartões obtidos de vendedores, revendedores ou distribuidores **não autorizados**, inclusive sites de leilão, "não são válidos e não serão honrados". Os códigos são específicos por região — [Roblox – Termos de gift cards (Singapura)](https://en.help.roblox.com/hc/en-us/articles/16719896592788-SINGAPORE-TERMS-AND-CONDITIONS-FOR-ROBLOX-GIFT-CARDS-AND-CREDITS); [EndGameTools – Roblox gift cards](https://endgametools.com/en/blog/roblox-gift-cards)
- Guias comerciais listam Eneba, Loaded, SEAGM, Gamivo e Kinguin como vendedores de códigos Roblox, mas nenhuma fonte mostra autorização da Roblox para eles — [Eneba Hub – Buy Robux](https://www.eneba.com/hub/cheap-in-game-currency/best-sites-to-buy-robux-online/); [PerfectGift – Where to buy Roblox](https://www.perfectgift.com/gift-guides/interest/where-to-buy/where-to-buy-roblox-gift-cards)
- A Celcoin (recarga "online", que credita direto) e a Hype Games (moeda virtual) são canais B2B brasileiros que incluem crédito de jogo — [Celcoin Developers](https://developers.celcoin.com.br/docs/sobre-recargas-nacionais); [JWave (2025)](https://www.jwave.com.br/2025/09/hype-games-ultrapassa-100-parceiros-e-mira-expansao-digital-no-brasil/)

### Inferences
- Um "Recarga Jogo próprio" não é viável para uma loja pequena. O realista é revender diamantes, Robux e afins **comprando de um agregador oficial**: programa de revenda Codashop, OMS da Razer Gold (exige empresa registrada + canal de vendas) ou Hype Games/Celcoin no Brasil. Nesse modelo a loja compete em conveniência (Pix, WhatsApp, atendimento) e não em preço, porque o próprio site oficial dá bônus (10% no Recarga Jogo).
- Robux é a categoria em que "fornecedor não autorizado" pesa mais, porque os termos da Roblox anulam cartões de revendedores não autorizados.
- Top-up por ID/UID (sem senha) é mais seguro do que pedir login do cliente. Também casa melhor com entrega automática via API.

### Gaps
- Não pesquisei (limite de buscas): **PUBG Mobile UC (Midasbuy/Tencent), Mobile Legends (Moonton), Valorant/Riot Points** e as listas oficiais de parceiros de cada publisher.
- Não encontrei margens, depósito mínimo ou critérios de aceitação do Programa de Revenda Codashop nem da distribuição Razer Gold para um CNPJ brasileiro.
- Não confirmei se a própria Garena tem um programa de revenda B2B no Brasil fora dos agregadores.

## 3. Game keys: distribuidores autorizados vs. gray market, restrições regionais e riscos

### Takeaway
Keys de marketplaces (G2A, Kinguin, Eneba) vêm em boa parte de atacadistas cuja origem o comprador final não controla. Há caso documentado de **revogação em massa** de keys compradas com cartão roubado: Ubisoft, 2014–2015. Para uma loja que responde ao consumidor brasileiro, o risco de revogação, chargeback e região errada recai sobre ela. A recomendação é comprar só de distribuidor autorizado com nota fiscal e exigir "prova de origem".

### Cited Findings
- Em 2014–2015 a Ubisoft revogou keys Uplay de jogos como Far Cry 4 e Assassin's Creed Unity compradas em revendedores como G2A e Kinguin. Segundo a Ubisoft, confirmada depois pela EA, as keys tinham sido compradas na Origin com cartão de crédito roubado — [KitGuru](https://www.kitguru.net/gaming/matthew-wilson/revoked-ubisoft-keys-were-bought-from-origin-with-stolen-credit-cards/); [PC Gamer](https://www.pcgamer.com/ubisoft-says-canceled-uplay-game-keys-were-fraudulent/); [TechRaptor](https://techraptor.net/gaming/news/update-ubisoft-removes-keys-uplay-purchased-grey-market)
- A Ubisoft depois reativou as keys de quem já tinha ativado e começado a jogar. Keys ainda não ativadas não voltaram a funcionar, e parte dos compradores não recebeu reembolso — [KitGuru – reinstates](https://www.kitguru.net/gaming/matthew-wilson/ubisoft-reinstates-fraudulent-keys-bought-with-stolen-credit-card/); [Slashdot (jan/2015)](https://games.slashdot.org/story/15/01/27/0012208/ubisoft-revokes-digital-keys-for-games-purchased-via-unauthorised-retailers)
- Na época, observadores disseram que parte das keys parecia vir de arbitragem de preço regional, não de fraude, então a causa exata ficou em disputa — [Slashdot (2015)](https://games.slashdot.org/story/15/01/27/0012208/ubisoft-revokes-digital-keys-for-games-purchased-via-unauthorised-retailers)
- Um tópico de fórum de 2024 sobre Helldivers 2 relata key invalidada depois que o cartão usado na compra foi dado como roubado. É relato de usuário, não declaração do publisher — [Steam Community – Helldivers 2](https://steamcommunity.com/app/553850/discussions/1/4206994473254255793/?ctp=3)
- A G2A admite que a maioria das keys vem de "atacadistas verificados" que compram em volume, e que a verificação de vendedor pode exigir prova de origem — [G2A – Source of keys](https://supporthub.g2a.com/marketplace/en/G2A-Services/what-is-the-source-of-the-keys-on-g2a); [G2A – How key marketplaces work](https://supporthub.g2a.com/marketplace/en/G2A-Services/how-key-marketplaces-work)
- A Eneba diz que só pode vender quem compra de distribuidores oficiais e que as keys da plataforma não se destinam à revenda — [Eneba – Can I buy from other vendors and resell](https://www.eneba.com/support/article/can-buy-other-vendors-resell)
- Cartões Steam Brasil (BRL) estão sujeitos ao Steam Subscriber Agreement — [Bitrefill – Steam Brazil](https://www.bitrefill.com/cn/en/gift-cards/steam-brazil/)
- Um artigo de 2026 sobre revenda de Apple Gift Card diz que a Apple não tem programa oficial de revenda e que seus termos proíbem a revenda. A fonte é comercial e fraca — [BitTopup News (2026)](https://news.bittopup.com/news/bulk-apple-gift-card-reseller-strategies-2026-wholesale-discounts-instant-delivery-margin-maximization)
- Códigos Roblox são específicos por região, e o cartão tem de bater com a região da conta — [EndGameTools](https://endgametools.com/en/blog/roblox-gift-cards)

### Inferences
- **Sinais de alerta de gray market:** preço abaixo do custo oficial, ausência de nota fiscal/contrato, keys "global" de jogos que só vendem por região, vendedor que não informa a origem, e keys de jogos recém-lançados vendidas muito barato.
- **Mitigações:** comprar só de distribuidor com contrato (ex.: Hype Games, que lista Sony, Microsoft e Ubisoft como parceiros em 2021). Guardar nota e lote de cada key. Vender só keys de região BR ou "global" confirmada. Deixar claro no anúncio a plataforma e a região de ativação. Ter política de reposição para key inválida.
- Keys de jogos de PC têm margem baixa e competem com Nuuvem, Steam e as próprias promoções. Para dois sócios, a relação risco/retorno parece pior que a de gift cards BRL de distribuidor oficial (inferência).

### Gaps
- Não encontrei uma política atual (2026) de revogação de Ubisoft, EA, Valve ou Sony, nem dados sobre a frequência de revogações recentes.
- Não pesquisei distribuidores autorizados de keys de PC no Brasil (ex.: Nuuvem B2B), por causa do limite de buscas.

## 4. Contas e itens in-game: como vendedores profissionais se abastecem, riscos de contas roubadas/recuperáveis e verificação

### Takeaway
Vender contas viola os Termos de Serviço dos principais publishers. A Riot proíbe expressamente compra, venda e compartilhamento de contas e, desde 10/09/2025 (patch 25.18), caça contas compradas no LoL. Comprar contas em geral não é crime, mas a consequência vem do publisher, que pode banir. Não encontrei fontes sobre como vendedores profissionais se abastecem nem sobre como verificar o histórico de uma conta antes de comprá-la.

### Cited Findings
- A Riot chama compartilhar e vender conta de "proibição firme", sujeita a banimento imediato, e diz que o anti-cheat Vanguard ajuda a detectar contas compartilhadas, vendidas ou botadas (2025) — [League of Legends /dev – Banning bots, boosters & more in 2025](https://www.leagueoflegends.com/en-us/news/dev/dev-banning-bots-boosters-and-more-in-2025/)
- A partir do patch 25.18 (10/09/2025), a Riot passou a mirar contas de smurf, boostadas e **compradas** no LoL e anunciou revisão de dados históricos (contas botadas desde 2017). Contas alternativas legítimas não seriam afetadas — [Tribune (2025)](https://tribune.com.pk/story/2561064/league-of-legends-to-ban-thousands-of-smurf-and-bought-accounts-in-major-crackdown); [League of Legends /dev (2025)](https://www.leagueoflegends.com/en-us/news/dev/dev-banning-bots-boosters-and-more-in-2025/)
- O suporte do LoL mantém o artigo "Don't Buy Accounts" — [LoL Support – Don't Buy Accounts](https://support-leagueoflegends.riotgames.com/hc/en-us/articles/202290340-Don-t-Buy-Accounts)
- Desde a atualização de termos de dez/2024, criadores patrocinados por sites de boosting ou que promovem compra e venda de contas podem ter a conta Riot suspensa — [Riot Games – Creator-related updates](https://www.riotgames.com/en/news/creator-related-updates-riot-privacy-notice-terms-of-service); [Dexerto](https://www.dexerto.com/gaming/new-riot-games-policy-can-get-lol-valorant-streamers-banned-for-their-sponsors-2992736/)
- Um site comercial de contas diz que comprar conta é, em geral, legal em muitas jurisdições, mas viola os ToS do publisher, e que a consequência vem do publisher, não da Justiça. A fonte é parcial — [AccountShark (2026)](https://accountshark.net/blog/is-buying-gaming-accounts-legal-2026)
- A GGMax tem conteúdo de blog voltado a quem vende contas ("5 dicas para vender sua conta de jogo online rapidamente"), o que confirma a categoria como central na plataforma — [Blog GGMax](https://ggmax.com.br/blog/5-dicas-para-vender-sua-conta-de-jogo-online-rapidamente)

### Inferences
- Toda revenda de conta depende de violar o ToS do publisher, inclusive de conta "self-farmed", porque o problema é a transferência em si. Esta categoria deve ser marcada como **dependente de violação de ToS** no relatório.
- Riscos de comprar contas de terceiros para revender (conhecimento geral; não houve fonte nesta pesquisa):
  - **Recuperação pelo dono original:** o dono pode reaver a conta pelo suporte, com e-mail de criação, comprovantes de compra ou dados de primeiro login.
  - **Origem criminosa:** a conta pode ter sido roubada ou obtida por phishing.
  - **Chargeback:** compras feitas com cartão roubado podem ser estornadas.
  - **Banimento retroativo.**
- Verificações costumam incluir:
  - entregar o **e-mail de criação** junto com a conta;
  - checar o histórico de alterações de e-mail e senha;
  - pedir comprovantes de compras in-game;
  - checar vínculos com terceiros (Facebook/Google/Apple);
  - checar penalidades anteriores.
  
  Tudo isso precisa ser confirmado com fontes específicas.
- Para dois sócios, contas próprias farmadas pelos sócios reduzem o risco de recuperação, mas não o de banimento.

### Gaps
- Não pesquisei (limite de buscas): fornecedores de contas em volume, a prática de "contas full acesso" no Brasil, golpes de recuperação de conta (ex.: Free Fire vinculado ao Facebook) e roteiros de verificação de histórico. Nenhum fato desta categoria além dos ToS da Riot tem fonte.
- Não verifiquei as regras de Garena, Epic, Activision ou Roblox sobre venda de contas.
- Não verifiquei o enquadramento jurídico no Brasil (CDC, responsabilidade do vendedor por conta recuperada).

## 5. Boosting/coaching: como montar equipe, modelos de pagamento, controle de qualidade e risco de ban

### Takeaway
Para a Riot, boosting é login de um jogador na conta de outro para jogar ranqueadas. É proibido pelos ToS e punível com restrição, suspensão ou ban, e o Vanguard ajuda na detecção. Coaching sem acesso à conta não entra nessa definição. Não encontrei fontes sobre como as lojas montam e pagam a equipe de boosters e coaches.

### Cited Findings
- A Riot define boosting como "manipulação de rank em que um jogador mais habilidoso (booster) entra na conta de outro (boostee) para jogar ranqueadas, devolvendo a conta ou não", e diz que isso viola os Termos de Serviço — [League of Legends /dev (2025)](https://www.leagueoflegends.com/en-us/news/dev/dev-banning-bots-boosters-and-more-in-2025/)
- A Riot afirma que vai restringir, suspender ou banir contas envolvidas e que o Vanguard ajuda a detectar contas compartilhadas e vendidas — [League of Legends /dev (2025)](https://www.leagueoflegends.com/en-us/news/dev/dev-banning-bots-boosters-and-more-in-2025/)
- Conteúdo que promova boosting ou troca de contas está sujeito a penalidade (termos de dez/2024) — [Riot Games – Creator-related updates](https://www.riotgames.com/en/news/creator-related-updates-riot-privacy-notice-terms-of-service)
- Guias de terceiros acrescentam que as penalidades podem incluir reset de rank e perda de recompensas. São fontes secundárias e comerciais — [GGClan (2026)](https://ggclan.com/news/is-valorant-boosting-bannable-2026-rules-what-to-do-instead); [LoLBoost](https://lolboost.gg/blog/is-lol-elo-boosting-safe-in-2025-key-facts-and-safety-tips)

### Inferences
- **Boosting com login na conta do cliente** = serviço que depende de violar ToS, com risco de ban da conta do **cliente**. Isso gera disputa e reembolso para a loja. Classifique como alto risco.
- **Coaching** (aula, análise de replay, duo sem compartilhar conta) não se encaixa na definição da Riot. É a alternativa de menor risco para dois sócios que joguem bem (inferência a partir da definição; não verifiquei se jogar duo pago tem regra própria em cada jogo).
- Modelos usuais de remuneração de boosters (porcentagem por pedido, valor por divisão) e controle de qualidade (stream do jogo, VPN da região do cliente, prazo por divisão) **não têm fonte nesta pesquisa**.

### Gaps
- Equipe, pagamento, contratação de boosters/coaches no Brasil, controle de qualidade e taxas de ban reais: não pesquisado (limite de buscas).
- Regras específicas de Garena (Free Fire), Valve (CS2), Activision e Epic sobre boosting: não pesquisado.

## 6. Automação de entrega: estoque/API no checkout, cofre de credenciais, revelação única, e-mail/WhatsApp, alertas, falhas, reembolsos, SLA; e a "entrega automática" da GGMax

### Takeaway
A "entrega automática" da GGMax é **estoque pré-cadastrado** (código ou credencial) que a plataforma libera ao comprador quando o pagamento é aprovado. O pagamento ao vendedor só é liberado depois que o comprador confirma o recebimento e passa um prazo de segurança. As APIs de fornecedores trazem padrões que a loja própria precisa copiar:
- "declared stock" + eventos de reserva (Kinguin);
- polling + conciliação por arquivo, sem webhook (Celcoin);
- cobrança só após entrega bem-sucedida (Bamboo);
- whitelist de IP + token (EZ PIN).

### Cited Findings
**GGMax**
- No blog da GGMax, "entrega automática" significa que o vendedor cadastra o item antes da venda e ele é entregue automaticamente após a compra. O blog diz que o recurso exige o **Plano MAX** e que ativá-lo "aumenta a chance de venda em mais de 70%" (alegação promocional). O "estoque automático" é o pré-cadastro do produto a ser enviado quando o pagamento é aprovado (texto de ~2 anos, ~2024) — [Blog GGMax – Anúncios dinâmicos e Estoque Automático](https://ggmax.com.br/blog/anuncios-dinamicos-e-estoque-automatico-como-configurar-meu-anuncio)
- Os termos de uso da GGMax listam três planos com taxa sobre a venda: **Prata 9,99%, Ouro 11,99% e Diamante 12,99%**. Anunciar é grátis e a taxa só é cobrada se houver venda. Compras abaixo de R$ 25 pagam uma taxa operacional do comprador, que a GGMax pode alterar. Os nomes dos planos (Prata/Ouro/Diamante vs. "Plano MAX") não batem entre as fontes e as datas não estão claras — [GGMax – Termos de uso](https://www.ggmax.com.br/termos-de-uso); [GGMax – Tarifas e prazos](https://ggmax.com.br/tarifas-e-prazos)
- O comprador confirma o recebimento e a plataforma libera o pagamento ao vendedor após um prazo de segurança — [GGMax – Tarifas e prazos](https://ggmax.com.br/tarifas-e-prazos); [GGMax – Como funciona](https://ggmax.com.br/como-funciona)
- Há calculadoras de taxa de terceiros (não oficiais) para vendedores da GGMax — [Calculadora GGMAX (terceiro)](https://calculadora-ggmax.vercel.app/)

**Padrões das APIs de fornecedores**
- **Kinguin – declared stock:** o vendedor declara o estoque de uma oferta via PATCH e escuta eventos de **reserva** quando há compra; a key só é fornecida nesse momento. Os webhooks podem ser protegidos por token no cabeçalho. A documentação avisa que **a ordem dos eventos não é garantida**, então o consumidor precisa tolerar eventos fora de ordem — [Kinguin Seller Hub – Sellers API](https://kinguin-seller-hub.document360.io/docs/publicapidocumentationv2)
- **Eneba** também oferece automação "Declared Stock" na API de comerciante — [Eneba API docs](https://api.eneba.com/documentation/)
- **Celcoin:** sem webhooks (status por consulta), com arquivo SFTP das recargas do dia anterior para conciliação. PIN entregue ao usuário ou crédito online direto — [Celcoin Developers – Realizar uma recarga](https://developers.celcoin.com.br/docs/realizar-uma-recarga); [Celcoin Developers – Sobre recargas](https://developers.celcoin.com.br/docs/sobre-recargas-nacionais)
- **Bamboo:** cobra só depois que o gift card é entregue com sucesso, o que reduz o risco de pagar por pedido que falhou — [Bamboo API](https://new.bamboo-card.com/bamboo-api/)
- **EZ PIN:** client ID/secret, whitelist de IP, token em todas as requisições, webhooks e sandbox — [EZ PIN – API v2.0](https://ezpin.com/blog/ez-pin-api-version-2-0-announced-complete-guide/)
- **Reloadly:** o pedido pode mandar o código direto ao e-mail e ao telefone do destinatário — [Reloadly – How to order a gift card](https://reloadly.com/blog/?p=2787)
- **Top-up por UID:** a LootBar leva tipicamente 3–5 minutos sem pedir senha. O Recarga Jogo aceita login só com o ID. Boleto pode levar ~3 dias úteis para compensar — [LootBar – blog](https://lootbar.gg/blog/en/lootbar-top-up-cheap-fast-safe.html); [Bolavip (2022)](https://br.bolavip.com/games/Free-Fire-conheca-o-Recarga-Jogo-site-oficial-para-comprar-diamante-por-PIX-cartao-e-boleto--Games-20220222-0132.html); [TechTudo (2019)](https://www.techtudo.com.br/dicas-e-tutoriais/2019/06/o-site-recarga-jogo-e-confiavel-veja-como-funciona-com-free-fire.ghtml)
- Produtos de top-up costumam ser vendidos como **não reembolsáveis** depois de entregues (ex.: StartSelect) — [StartSelect](https://startselect.com/pt-pt/free-fire-1080-diamonds/72119)
- O plugin WooCommerce da Kinguin (desatualizado há mais de 2 anos) tem relatos de falha na entrega de keys. Plugins de terceiros não substituem testes ponta a ponta — [WordPress.org – Kinguin plugin](https://en-za.wordpress.org/plugins/kinguin/)

### Inferences
(Recomendações de arquitetura derivadas dos padrões acima e de boas práticas gerais. Não há fonte específica para cada item.)
- **Dois modos de entrega:**
  - **(a) estoque próprio pré-comprado**, para cartões de alto giro como PSN e Xbox BRL de valores populares: entrega instantânea, mas o capital fica parado e há risco de perda;
  - **(b) compra just-in-time via API no checkout**, para catálogo longo e top-ups por UID: sem estoque parado, mas depende do uptime do fornecedor.
  
  O ideal é um híbrido com fallback de um modo para o outro.
- **Gatilho de entrega:** só depois da confirmação do pagamento (webhook do PSP). Pix é praticamente imediato, boleto leva dias, e cartão tem risco de chargeback. Para cartão, convém um antifraude e um atraso ou limite para clientes novos.
- **Cofre de códigos e credenciais:**
  - criptografia em repouso (ex.: AES-GCM com chave em KMS);
  - acesso só pelo serviço de entrega;
  - log de quem viu cada código;
  - **revelação única** na área do cliente com registro de data, hora e IP. Isso serve de prova em disputas de "não recebi".
- **Canais:** área do cliente como fonte de verdade, mais e-mail transacional e WhatsApp (API oficial do WhatsApp Business) com link para a revelação. Evite mandar o código em texto puro por canais de terceiros.
- **Idempotência:** chave de idempotência por pedido nas chamadas ao fornecedor. Como a Celcoin não tem webhook e a Kinguin não garante a ordem dos eventos, é preciso polling com backoff, uma máquina de estados (pago → solicitado → entregue/falhou) e conciliação diária (o arquivo SFTP da Celcoin serve para isso).
- **Falhas:** fila de reprocessamento. Depois de N tentativas, o pedido vai para atendimento humano, com reembolso automático via Pix (estorno) se não houver entrega em X minutos. Defina um SLA público, por exemplo "até 15 min, 24/7", e acompanhe o tempo médio.
- **Alerta de estoque baixo e saldo:** limite mínimo por SKU e alerta quando o saldo pré-pago em cada fornecedor estiver abaixo de N dias de vendas, com aviso por WhatsApp ou e-mail aos sócios.
- **Escrow próprio:** a GGMax segura o pagamento até a confirmação do comprador. Uma loja própria não precisa disso, mas deve guardar logs de entrega para responder a chargebacks.

### Gaps
- Não consegui ler o conteúdo atual da central de ajuda da GGMax (WebFetch falhou). Ficaram sem confirmação: prazo exato de liberação, plano exigido em out/2026 e regras de disputa.
- Não pesquisei regras do CDC (direito de arrependimento em compras online) aplicadas a bens digitais entregues na hora, nem requisitos da API oficial do WhatsApp Business.
- Não encontrei SLAs publicados pelos fornecedores (Celcoin, RV, Hype, Reloadly).

## 7. Benchmarks de margem por categoria e melhor relação margem/risco para uma loja de dois sócios

### Takeaway
As margens publicadas de gift cards e créditos de jogos são **baixas e opacas**:
- os poucos números genéricos de atacado ficam entre ~2% e 15% abaixo do valor de face, com média de comissão ~5% em um agregador;
- uma tabela comercial brasileira mostra 11–14% sem fonte;
- distribuidores raramente divulgam seus descontos.

Não encontrei números confiáveis para contas, boosting ou keys. A combinação de menor risco é **gift cards BRL e top-ups por UID de distribuidor oficial**, com margem baixa e competição em conveniência. Contas e boosting podem ter margem maior, mas dependem de violar ToS.

### Cited Findings
- Um guia de revenda descreve a lógica de comprar em volume abaixo do valor de face (exemplo: cartão de US$ 100 por US$ 90) — [Reloadly – Gift card reseller program](https://www.reloadly.com/blog/gift-card-reseller-program/)
- Uma página do Alibaba diz que o preço de atacado de gift cards costuma ficar 5–15% abaixo do valor de face. A fonte é fraca e genérica — [Alibaba – Gift card distributors](https://www.alibaba.com/product-insights/gift-card-distributors.html)
- Um agregador (Finperks) relata comissão bruta média de fornecedor de cerca de 5% no catálogo, chegando a 9% em algumas marcas. É fonte comercial — [Finperks – Best margins on gift cards](https://finperks.com/post/best-margins-on-gift-cards-for-a-marketplace-or-retailer-orchestration); [Finperks – Gift card margin model](https://finperks.com/post/how-does-the-gift-card-margin-model-work-and-who-funds-the-cashback)
- A Giftbit (agregador) diz que é "incrivelmente raro" um distribuidor revelar os descontos que recebe dos fornecedores — [Giftbit – Distributor pricing](https://www.giftbit.com/blog/gift-card-distributor-pricing)
- Apple: o canal B2B não dá desconto, e o desconto realista em volume nos EUA fica em 2–15%. Fonte comercial de 2026 — [BitTopup News (2026)](https://news.bittopup.com/news/bulk-apple-gift-card-reseller-strategies-2026-wholesale-discounts-instant-delivery-margin-maximization)
- Uma lista comercial brasileira diz que gift cards de Free Fire, PlayStation, Xbox e Steam têm "alta demanda e boa margem" e traz tabela de exemplo com margens de **11% a 14%**, sem fonte verificável — [Vivendo Marketing](https://vivendomarketing.com/5-fornecedores-de-gift-card-confiaveis-para-revender/)
- Referências genéricas de varejo (não específicas de gift cards): margem de revenda "ideal" de 30–100% segundo a Loja Integrada, e de 30–50% segundo a InfinitePay. A margem de distribuidor varia de 3% a 30% — [Loja Integrada](https://lojaintegrada.com.br/hub/qual-a-margem-de-lucro-ideal-para-revenda/); [InfinitePay](https://www.infinitepay.io/materiais/calculadora-de-margem-de-lucro); [Exporteers](https://exporteers.com/pt-pt/distributor-margin/)
- Custo de canal se vender também na GGMax: taxa de 9,99% a 12,99% por venda, conforme o plano — [GGMax – Termos de uso](https://www.ggmax.com.br/termos-de-uso)
- O canal oficial concorre com bônus próprio: o Recarga Jogo dava 10% de diamantes extras (2022) — [Bolavip (2022)](https://br.bolavip.com/games/Free-Fire-conheca-o-Recarga-Jogo-site-oficial-para-comprar-diamante-por-PIX-cartao-e-boleto--Games-20220222-0132.html)

### Inferences
Matriz qualitativa margem × risco (inferência a partir das seções 1–6; os números de margem **não estão confirmados**):

| Categoria | Margem bruta provável | Risco legal/ToS | Risco operacional | Observação |
|---|---|---|---|---|
| Gift cards BRL (PSN, Xbox, Steam, Google Play) de distribuidor nacional | Baixa (um dígito a ~14%, não confirmado) | Baixo | Chargeback/fraude no pagamento | Melhor base de catálogo; automatizável 100% |
| Top-up por UID (Free Fire, Genshin etc.) via agregador oficial | Baixa | Baixo | Fornecedor fora do ar; UID errado | Compete com bônus do site oficial; vantagem é Pix/atendimento |
| Robux via cartão de revendedor autorizado | Baixa | Médio se a origem não for autorizada (a Roblox anula) | Região | Só com fornecedor comprovadamente autorizado |
| Keys de PC de marketplace (G2A/Kinguin/Eneba) | Variável | **Gray market** | Revogação, key inválida | Evitar como fonte; no máximo como canal de venda |
| Contas (self-farmed ou compradas) | Potencialmente alta (sem dado) | **Viola ToS** | Recuperação pelo dono, ban | Só com política de garantia e muita cautela |
| Boosting com login | Potencialmente alta (sem dado) | **Viola ToS** | Ban da conta do cliente → reembolso | Alto risco |
| Coaching sem login | Depende da hora do sócio | Baixo | Escala limitada | Opção legítima de serviço |

- Para dois sócios, a recomendação inferida é começar com (1) gift cards BRL e (2) top-ups por UID via um ou dois agregadores com API, já que exigem pouco trabalho por pedido. Coaching pode entrar como serviço premium. Contas e boosting devem ficar fora do lançamento ou isolados, com aviso explícito ao cliente de que dependem de violar ToS.
- Margem baixa exige volume. Taxa de PSP (Pix é mais barato que cartão), impostos (Simples Nacional) e taxa de marketplace (9,99–12,99% na GGMax) podem anular uma margem de um dígito. Vender gift cards na GGMax a preço de face provavelmente dá prejuízo (inferência a partir das taxas citadas).

### Gaps
- Nenhuma fonte primária trouxe o **desconto real** dado por Celcoin, RV Hub, Hype Games, Razer Gold ou Codashop a revendedores no Brasil. Isso precisa de cotação direta.
- Não encontrei benchmarks de margem para contas, itens in-game, boosting ou coaching no Brasil.
- Não verifiquei a alegação, vista em resultado de busca, de que o PROCON imporia teto de margem de 20%. Ela parece sem fonte oficial.
