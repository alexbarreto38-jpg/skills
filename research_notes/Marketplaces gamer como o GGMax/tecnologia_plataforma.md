# Tecnologia e arquitetura da plataforma (loja/marketplace de produtos digitais gamer tipo GGMax)

> **Nota de método (12/10/2026):** o ambiente desta pesquisa tinha forte restrição de rede. (1) Pedidos HTTP diretos a ggmax.com.br, g2g.com, eldorado.gg, playerauctions.com e eneba.com foram **recusados pelo proxy (403 CONNECT)**, então **não foi possível ler cabeçalhos HTTP nem o HTML desses sites**. (2) BuiltWith, Wappalyzer, Workana, Lever, vercel.com, cloudflare.com, supabase.com, fly.io, railway.com, developers.facebook.com e planalto.gov.br **não resolveram** no WebFetch. (3) O orçamento de buscas web (compartilhado entre agentes) **esgotou-se** no meio da pesquisa. Por isso: preços e documentação de fornecedores foram lidos **no repositório oficial de documentação de cada fornecedor no GitHub** (cloudflare-docs, superfly/docs, railwayapp/docs, supabase/supabase) ou em cloud.google.com, que estava acessível. Fatos marcados com "(via resumo de busca)" vêm do resumo do mecanismo de busca sobre a URL citada, não de leitura direta da página. Itens marcados "[não verificado nesta sessão]" citam a fonte canônica, mas não foi possível reabri-la.

## 1. Que tecnologia o GGMax e os principais concorrentes (G2G, Eldorado.gg, PlayerAuctions, Eneba) parecem usar?

### Takeaway
Há evidência pública sólida apenas para a **Eneba**: backend PHP/Symfony com Go, GraphQL, CQRS com Saga/Temporal, mais de 100 microsserviços em Kubernetes na AWS e frontend React/TypeScript. Para **GGMax, G2G, Eldorado.gg e PlayerAuctions** não consegui obter cabeçalhos HTTP, relatórios BuiltWith/Wappalyzer nem vagas que revelem a stack. O que se sabe do GGMax é o **modelo de negócio** (comissão por plano, retenção de saldo em escrow de 4 a 7 dias, prazo de análise de até 180 dias), não a tecnologia.

### Cited Findings
**GGMax (Brasil)**
- O SimilarWeb lista 34 tecnologias detectadas para ggmax.com.br, entre elas Instagram e G Suite para e-mail. A lista completa fica atrás de exportação paga, e a página é datada de agosto de 2026 (via resumo de busca) — [SimilarWeb](https://www.similarweb.com/website/ggmax.com.br/)
- O GGMax se descreve como intermediário que garante segurança ao comprador. Os termos de uso o definem como "plataforma tecnológica de intermediação" entre compradores e vendedores (via resumo de busca) — [FAQ GGMax](https://ggmax.com.br/perguntas-frequentes); [Termos de uso](https://www.ggmax.com.br/termos-de-uso)
- Comissões por plano do vendedor: Prata 9,99%, Ouro 11,99% e Diamante 12,99% sobre o valor da venda. Anunciar é grátis; a taxa só incide na venda (via resumo de busca dos termos) — [Termos de uso](https://www.ggmax.com.br/termos-de-uso). Os mesmos percentuais aparecem num projeto de terceiros no GitHub, que também simula uma taxa de saque Pix de R$ 2,00 — [calculadora-de-taxas-ggmax (GitHub)](https://github.com/muriloatavares/calculadora-de-taxas-ggmax)
- Prazos-padrão de liberação do saldo ao vendedor (escrow): **4 dias** para moedas, gold, itens, contas sem e-mail verificado e cursos, e **7 dias** para contas, powerleveling e serviços. O prazo cai pela metade se o comprador marcar o item como entregue e avaliar o vendedor positivamente (via resumo de busca) — [Tarifas e prazos GGMax](https://ggmax.com.br/tarifas-e-prazos)
- Os termos dizem que a análise "pode se estender até 180 dias" quando necessário e que nenhum plano reduz o prazo de liberação. O "Plano MAX" só encurta o processamento do saque (via resumo de busca) — [Termos de uso](https://www.ggmax.com.br/termos-de-uso)
- Vendedores reclamam de retenções maiores, por exemplo de 7 para 21 dias. Em resposta pública, o GGMax disse que algumas categorias têm prazos especiais e que o prazo de contas Supercell mudou após alterações nas políticas de segurança da Supercell (via resumo de busca) — [Reclame Aqui – 7 para 21 dias](https://www.reclameaqui.com.br/ggmax/prazo-de-liberacao-de-saldo-alterado-de-7-para-21-dias-apos-venda_mXO7UcrQbd2WIb10/); [Reclame Aqui – 21 dias](https://www.reclameaqui.com.br/ggmax/21-dias-pra-liberar-o-dinheiro-da-venda_L_qdmWMNG-vqQayF/)
- Nota "Poor" de 2,6/5 no Trustpilot (via resumo de busca) — [Trustpilot](https://www.trustpilot.com/review/ggmax.com.br)
- A busca de repositórios por "ggmax" no GitHub retorna 82 resultados. Entre eles: "GGMAXFAKE" ("GGMAX FAKE", arquivado), bots de automação ("auto-_ggmax_", "Bot-discord – Aprovação GGMAX") e vários sites "primeira venda 24h – GGMAX academy" — [GitHub search "ggmax"](https://github.com/search?q=ggmax&type=repositories)
- Existe pelo menos um projeto freelance (Workana, março de 2024) pedindo um "site de intermediação de vendas inspirado em ggmax.com.br", na operação e no design (via resumo de busca; não consegui abrir a página para ver orçamento e propostas) — [Workana](https://www.workana.com/job/desenvolvimento-de-site-de-intermediacao-de-vendas-inspirado-em-ggmax-com-br)

**Eneba (Lituânia)** — a evidência mais forte
- Vaga "Backend Engineer, PHP": PHP/Symfony como linguagem principal e Golang como secundária, "usada onde a velocidade importa". GraphQL é o principal meio de comunicação, entre serviços e entre frontend e serviços (via resumo de busca) — [Eneba – Lever](https://jobs.eu.lever.co/eneba/7e8ef892-36b8-4a2d-970b-d19e136a581c); [Symfony Jobs](https://symfony.com/jobs/3bd882f)
- A arquitetura é CQRS: comandos via Saga/Temporal e consultas via GraphQL, com mais de 100 microsserviços. Infraestrutura: Kubernetes, Helm, AWS e Terraform. Bancos: MariaDB, MySQL, Redis, Elasticsearch e InfluxDB. CI/CD com mais de 50 deploys por dia (via resumo de busca) — [Eneba – Lever](https://jobs.eu.lever.co/eneba/7e8ef892-36b8-4a2d-970b-d19e136a581c)
- Há uma vaga dedicada "Backend Engineer, Security" (PHP/Symfony, Kubernetes e Helm, com foco em política de segurança entre times), o que indica um time de AppSec interno (via resumo de busca) — [Eneba – Lever (Security)](https://jobs.eu.lever.co/eneba/d12a7fe5-58e7-4039-9cc0-9b96bd97f9b8)
- Frontend: a vaga pede 3+ anos de React, "preferencialmente com TypeScript". Os times incluem design, backend, frontend, mobile e dados, apoiados por um time de platform engineering. O marketplace atende "10m+ usuários ativos" (via resumo de busca) — [javascript.jobs – Eneba](https://javascript.jobs/job/frontend-engineer-react-16)
- Faixas salariais: €55.000–66.000/ano numa vaga Symfony de agosto de 2025, €45.000–70.000 numa vaga UE e £70.000–110.000 na vaga de segurança listada no Reino Unido (via resumo de busca) — [Symfony Jobs](https://symfony.com/jobs/3bd882f); [remoteitjobs – Security](https://www.remoteitjobs.app/job/eneba-backend-engineer-security)

**Eldorado.gg (Lituânia)**
- Marketplace de moedas, contas, itens e serviços de jogos, fundado em 2018, com sede em Vilnius e cerca de 101–200 funcionários (via resumo de busca) — [Prospeo](https://prospeo.io/c/eldorado-gg-email-format); [Built In](https://builtin.com/company/eldoradogg/teams)
- As vagas públicas encontradas eram de CRM, design gráfico e retenção. Nenhuma revelava a stack técnica (via resumo de busca) — [Djinni](https://djinni.co/jobs/?page=552)

**G2G e PlayerAuctions**
- Buscas por vagas e stack não retornaram nenhuma página da G2G nem da PlayerAuctions. Os resultados eram de outras empresas — [busca sem resultado relevante; ver Gaps]

### Inferences
- O padrão da Eneba (CQRS, orquestração de sagas com Temporal, mais de 100 microsserviços, mais de 50 deploys por dia) reflete uma empresa com centenas de engenheiros e 10M+ usuários. **Não é um modelo para um MVP de 2 vendedores.** A lição útil é conceitual: tratar o pedido como um **workflow durável com compensações** (pagamento → reserva de estoque → entrega → liberação de escrow → estorno) e ter **AppSec dedicado** quando a operação crescer.
- O escrow do GGMax (4/7 dias, metade com avaliação positiva, até 180 dias em análise) é **regra de negócio no ledger** e não depende de tecnologia específica. Um clone precisa de carteira interna com estados "a liberar / disponível / sacado / bloqueado" e jobs agendados de liberação.
- Os repositórios "GGMAXFAKE" e os bots de automação mostram que a marca GGMax já atrai imitações e automações, um sinal de risco de phishing e fraude que o novo site também vai enfrentar.

### Gaps
- **Cabeçalhos HTTP, CDN, framework e hospedagem do GGMax, G2G, Eldorado.gg, PlayerAuctions e Eneba não foram verificados**: o proxy bloqueou os sites e o BuiltWith/Wappalyzer não estava acessível. Recomenda-se rodar a extensão Wappalyzer e `curl -I` a partir de uma máquina comum e procurar `server: cloudflare`, `cf-ray`, `x-powered-by`, `/_next/`, `__NUXT__`, `x-vercel-id`, `x-amz-cf-id` etc.
- Provedores de pagamento (PSP de Pix/cartão), chat e e-mail usados pelo GGMax: não encontrei evidência pública.
- Stack da G2G, Eldorado.gg e PlayerAuctions: nenhuma vaga ou blog técnico encontrado antes de o orçamento de buscas se esgotar.
- Orçamento e propostas do projeto Workana "inspirado em ggmax": página inacessível.

## 2. Opções de construção e trade-offs (custom, headless, SaaS/WooCommerce, plataformas de marketplace, scripts "clone")

### Takeaway
Para um MVP de 2 vendedores que deve virar marketplace com escrow, chat e reputação, os candidatos mais fortes são **(a) código próprio** (TypeScript: Next.js + NestJS ou Node, PostgreSQL e Redis) ou **(b) um motor headless open-source extensível em TypeScript**, como o **Medusa** (MIT, receita oficial de marketplace e de produtos digitais) ou o **Vendure** (GPLv3, plugin de exemplo multivendor com comissão da plataforma). Saleor (Python, BSD-3) é sólido, mas não tem multivendor nativo. WooCommerce + Dokan e Bagisto (Laravel) aceleram o lançamento, mas pioram o controle de segurança e da lógica de escrow e cofre. Scripts "clone" prontos são o maior risco.

### Cited Findings
**Headless open-source**
- **Medusa**: cerca de 36,7 mil estrelas no GitHub, núcleo sob licença MIT. Materiais de RBAC da "Enterprise Edition" exigem acordo comercial — [GitHub medusajs/medusa](https://github.com/medusajs/medusa)
- Medusa — receita oficial de marketplace: cria-se um "Marketplace Module" com modelos de vendedor e admins do vendedor, ligados a produtos e pedidos existentes. Os vendedores gerenciam seus pedidos separadamente — [Medusa Marketplace Recipe](https://github.com/medusajs/medusa/blob/develop/www/apps/resources/app/recipes/marketplace/page.mdx)
- Medusa — receita oficial de produtos digitais: um "Digital Product Module" ligado ao `ProductVariant`, com armazenamento via file module provider. Por padrão, "quando o cliente compra, um e-mail é enviado para download" — [Medusa Digital Products Recipe](https://github.com/medusajs/medusa/blob/develop/www/apps/resources/app/recipes/digital-products/page.mdx)
- **Vendure**: cerca de 8,5 mil estrelas, licença GPLv3, com exceção de licença para plugins e licença comercial disponível. Backend Node.js/NestJS/GraphQL e painel admin em React/TanStack — [GitHub vendure-ecommerce/vendure](https://github.com/vendure-ecommerce/vendure); [README Vendure](https://raw.githubusercontent.com/vendure-ecommerce/vendure/master/README.md)
- Vendure — plugin de exemplo de marketplace multivendor (APIs da v2.0), configurado com `platformFeePercent: 10` e com a mutation `registerNewSeller` na Shop API — [Vendure multivendor-plugin README](https://github.com/vendure-ecommerce/vendure/blob/master/packages/dev-server/example-plugins/multivendor-plugin/README.md)
- **Saleor**: cerca de 23,4 mil estrelas, licença BSD-3-Clause, plataforma "GraphQL native, API-only" em Python, com "native multichannel" (preço, moeda e estoque por canal). A página não menciona multivendor — [GitHub saleor/saleor](https://github.com/saleor/saleor)

**PHP/WordPress/Laravel prontos**
- **Dokan** (WooCommerce): plugin multivendor GPLv2+, versão estável 5.3.0, exige WordPress 7.0+, WooCommerce 8.5+ e PHP 7.4+. Cobra comissões de vendedores e se apresenta para "Digital Products Marketplace like Gumroad, Envato". Recursos adicionais ficam na "Pro Version" paga — [Dokan readme.txt](https://github.com/getdokan/dokan/blob/develop/readme.txt)
- **Bagisto**: plataforma open-source de e-commerce em Laravel com módulo de "Multi Vendor Marketplace" (gestão de vendedores, comissões, aprovação de produtos e pedidos). Há AMI pronta na AWS Marketplace — [GitHub bagisto/bagisto](https://github.com/bagisto/bagisto)

**Plataformas de marketplace**
- **Sharetribe**: o "Web Template" é um app React (create-react-app com SSR) para clonar e customizar sobre o backend hospedado da Sharetribe — [GitHub sharetribe/web-template](https://github.com/sharetribe/web-template)

**Scripts "clone"**
- No GitHub há repositórios como "GGMAXFAKE" (arquivado) e sites "GGMAX academy". Nenhum se apresenta como produto mantido e auditado — [GitHub search "ggmax"](https://github.com/search?q=ggmax&type=repositories)

### Inferences
- **Matriz de decisão (inferência do autor):**

| Opção | Tempo até MVP | Controle de segurança/escrow | Caminho para marketplace | Risco principal |
|---|---|---|---|---|
| Custom (Next.js + NestJS/Node ou Laravel; PostgreSQL + Redis) | Médio a alto | Total | Desenhado desde o início | Custo de desenvolvimento; disciplina de AppSec |
| Medusa (MIT, TS) | Médio | Alto (módulos próprios para cofre, carteira e escrow) | Receita oficial de marketplace | Atualizações de versão quebram customizações; RBAC avançado é comercial |
| Vendure (GPLv3, TS/NestJS) | Médio | Alto | Plugin de exemplo multivendor com taxa | GPLv3 exige atenção se o código for distribuído (SaaS não distribui, mas plugins e temas sim) |
| Saleor (Python, BSD-3) | Médio | Alto | Multivendor não nativo; exige construir | Stack Python/GraphQL; marketplace todo por conta própria |
| WooCommerce + Dokan / Bagisto | Baixo | Médio a baixo (superfície de plugins grande) | Pronto, porém genérico | Plugins de terceiros, escrow e cofre fracos, performance |
| Shopify / Nuvemshop + app de entrega digital | Muito baixo | Baixo (cofre e escrow fora do controle) | Ruim (não é marketplace multivendedor) | Lock-in; regras do app de entrega; não suporta P2P de contas |
| Sharetribe | Baixo | Médio (backend hospedado) | Nativo | Lock-in; modelo pensado para serviços e aluguéis, não para cofre de credenciais |
| Script "GGMax clone" | Muito baixo | Desconhecido ou nulo | Ilusório | Backdoors, licença duvidosa, cópia de marca/design (risco legal), sem manutenção |

- **Recomendação (inferência):** como segurança é diferencial, o produto central (cofre de entrega, ledger de carteira e escrow, chat com moderação, disputas) é o que **nenhum** motor entrega pronto. Isso favorece **código próprio em TypeScript** com bibliotecas maduras (Better Auth para autenticação, Centrifugo ou Socket.IO para chat, PostgreSQL como ledger) ou **Medusa como núcleo de catálogo, carrinho e checkout** com módulos próprios. Entre os dois: Medusa economiza catálogo, preço, promoções e admin; código próprio reduz a dependência e facilita modelar o ledger de duas pontas desde o primeiro dia.
- Lojas SaaS (Shopify/Nuvemshop) só fazem sentido se a fase 1 for **apenas venda de keys e gift cards próprios** sem P2P. Mesmo assim, a migração para marketplace seria uma reescrita.
- Vendure e Medusa usam TypeScript de ponta a ponta. Isso permite um único time e uma única linguagem para web, API, workers e chat.

### Gaps
- Preços atuais (2026) de Sharetribe, CS-Cart Multi-Vendor, Dokan Pro, Bagisto Multi-Vendor, Shopify e Nuvemshop, e de apps de entrega digital (ex.: apps de keys para Shopify/Nuvemshop): sites inacessíveis e orçamento de busca esgotado.
- Data e versão da última release de Medusa, Saleor e Vendure (as páginas capturadas não mostravam releases).
- Não encontrei avaliações independentes de scripts "GGMax clone" vendidos (CodeCanyon etc.).

## 3. Módulos necessários

### Takeaway
O núcleo que diferencia um site tipo GGMax de uma loja comum é: **(1) entrega automática por cofre criptografado** (KMS, revelação única, trilha de auditoria), **(2) ledger de carteira com escrow** e liberação agendada, **(3) chat em tempo real** vinculado ao pedido, com moderação, e **(4) disputas e reputação**. Catálogo, carrinho, checkout, cupons e SEO são commodity e podem vir de um motor headless.

### Cited Findings
- No GGMax, o vendedor só recebe depois do prazo de liberação (4 ou 7 dias, metade com avaliação positiva), e o prazo exato de cada venda aparece "no início do chat do pedido" ou no menu "Transações". Isso indica um chat atrelado ao pedido e uma carteira com saldo pendente (via resumo de busca) — [Tarifas e prazos GGMax](https://ggmax.com.br/tarifas-e-prazos); [Reclame Aqui](https://www.reclameaqui.com.br/ggmax/prazo-de-liberacao-de-saldo-alterado-de-7-para-21-dias-apos-venda_mXO7UcrQbd2WIb10/)
- Planos de vendedor com mais visibilidade (Diamante = "Máxima Visibilidade na Home") e prazos de liberação por categoria — [calculadora-de-taxas-ggmax](https://github.com/muriloatavares/calculadora-de-taxas-ggmax)
- Entrega digital no Medusa: módulo próprio ligado ao `ProductVariant`, arquivos via file module provider e envio por e-mail após a compra — [Medusa Digital Products Recipe](https://github.com/medusajs/medusa/blob/develop/www/apps/resources/app/recipes/digital-products/page.mdx)
- Chat em tempo real: o Centrifugo é um servidor PUB/SUB open-source, agnóstico de linguagem, com transportes WebSocket, HTTP-streaming, SSE, gRPC e WebTransport (experimental), e escala via Redis, PostgreSQL ou NATS. Ele é citado para "chat apps" — [GitHub centrifugal/centrifugo](https://github.com/centrifugal/centrifugo)
- Supabase Realtime (plano Pro): 500 conexões simultâneas de pico incluídas, depois US$ 10 por 1.000 — [Supabase billing](https://github.com/supabase/supabase/blob/master/apps/docs/content/guides/platform/billing-on-supabase.mdx)
- Autenticação: o Better Auth é um framework de autenticação e autorização para TypeScript, agnóstico de framework, licença MIT, com ecossistema de plugins para recursos avançados — [GitHub better-auth/better-auth](https://github.com/better-auth/better-auth)
- Multivendor com comissão da plataforma e registro de vendedor (para a fase marketplace) — [Vendure multivendor-plugin](https://github.com/vendure-ecommerce/vendure/blob/master/packages/dev-server/example-plugins/multivendor-plugin/README.md)

### Inferences
Lista de módulos com prioridade sugerida. **MVP** = loja de 2 vendedores; **F2** = abertura a terceiros.

| Módulo | Fase | Notas de implementação (inferência) |
|---|---|---|
| Catálogo por jogo, categoria e subcategoria, com variações (servidor, região, plataforma, quantidade) | MVP | Slugs SEO por jogo e categoria; atributos dinâmicos por categoria (JSONB no Postgres) |
| Busca e filtros | MVP | Postgres FTS + `pg_trgm` no MVP; Meilisearch, Typesense ou OpenSearch quando o catálogo crescer |
| Contas com 2FA (TOTP) e passkeys (WebAuthn) | MVP | Better Auth ou equivalente; verificação de senha vazada; sessões revogáveis |
| Carrinho e checkout | MVP | Checkout de um vendedor por pedido simplifica escrow e disputas |
| Pagamentos com webhooks | MVP | Pix (QR dinâmico) + cartão via PSP brasileiro; webhooks idempotentes (chave de idempotência, assinatura HMAC, reprocessamento); conciliação diária |
| Máquina de estados do pedido | MVP | `criado → aguardando_pagamento → pago → em_entrega → entregue → em_garantia → concluído`, com ramos `cancelado`, `em_disputa`, `reembolsado` e `chargeback`; transições só no servidor, com log |
| Entrega automática com cofre | MVP | Estoque de keys e credenciais cifrado com envelope encryption (chave de dados por item, chave mestra em KMS); revelação única para o comprador dono do pedido; log imutável de cada revelação (quem, quando, IP, dispositivo); mascaramento no admin |
| Carteira interna (ledger) | MVP (simples) → F2 (completo) | Partidas dobradas; saldos `pendente/disponível/bloqueado`; jobs de liberação por categoria (ex.: 4/7 dias como no GGMax); saque via Pix com antifraude |
| Chat em tempo real | MVP (comprador ↔ loja) → F2 (comprador ↔ vendedor) | WebSocket (Centrifugo, Socket.IO ou Supabase Realtime); chat por pedido; filtro de contato externo (telefone, Discord) para evitar evasão de taxa; anexos com antivírus; retenção para disputas |
| Avaliações e reputação | MVP (loja) → F2 (por vendedor) | Só pedidos concluídos avaliam; nível de vendedor; peso por valor e idade |
| Disputas e tickets | MVP | Disputa congela o escrow; SLA; evidências do chat e do log do cofre |
| Notificações | MVP | E-mail transacional; WhatsApp (templates de utilidade e autenticação); web push |
| Back-office admin | MVP | RBAC granular, 4-olhos para estornos e saques, trilha de auditoria |
| Cupons e afiliados | MVP (cupons) → F2 (afiliados) | Limites por usuário e antifraude de cupons |
| Analytics | MVP | Eventos de funil no servidor; consentimento LGPD para analytics de terceiros |
| Páginas SEO | MVP | SSR/ISR (Next.js) por jogo e categoria; sitemap; dados estruturados |
| Onboarding de vendedores (KYC), split de pagamento, planos de vendedor | F2 | KYC (documento + selfie), limites progressivos, planos de comissão estilo Prata, Ouro e Diamante |

### Gaps
- Não obtive documentação dos PSPs brasileiros (Mercado Pago, Pagar.me, Efí, Asaas, Stripe BR, Iugu) sobre split, escrow ("custódia") e webhooks, nem suas taxas atuais para Pix e cartão.
- Não obtive a política atual de templates do WhatsApp nem regras de moderação de chat em marketplaces gamer.

## 4. Arquitetura de segurança (ASVS, WAF/anti-bot, rate limiting, segredos, backups, logs, LGPD)

### Takeaway
Mirar o **OWASP ASVS 5.0 nível 2**, que exige MFA, verificação de senhas vazadas e reset que não contorne o MFA, e aplicar requisitos de **nível 3** ao cofre de entrega, à carteira e ao admin (autenticador por hardware/passkey para admins). Na borda, o **Cloudflare Pro** é o mínimo prático: o plano Free não tem o Managed Ruleset nem o OWASP Core Ruleset e só permite 1 regra de rate limiting de 10 s. **Turnstile** (grátis) protege cadastro, login e checkout.

### Cited Findings
**OWASP ASVS**
- A versão estável mais recente é a **5.0.0, de maio de 2025** — [GitHub OWASP/ASVS](https://github.com/OWASP/ASVS)
- O ASVS 5.0 tem 17 capítulos, de V1 a V17: Encoding/Sanitization, Validation/Business Logic, Web Frontend, API, File Handling, Authentication, Session, Authorization, Self-contained Tokens, OAuth/OIDC, Cryptography, Secure Communication, Configuration, Data Protection, Secure Coding/Architecture, Security Logging/Error Handling e WebRTC — [ASVS 5.0/en](https://github.com/OWASP/ASVS/tree/master/5.0/en)
- **L1** reúne cerca de 20% dos requisitos, o mínimo de "primeira camada de defesa". **L2**: "a maioria das aplicações deveria buscar este nível". Cerca de 50% dos requisitos são L2, então cumprir L2 exige cerca de 70% do ASVS (L1 + L2) — [ASVS 5.0 – What is the ASVS](https://github.com/OWASP/ASVS/blob/master/5.0/en/0x03-What-is-the-ASVS.md)
- "Aplicações L2 devem forçar o uso de MFA; aplicações L3 devem usar autenticação baseada em hardware" (6.3.3). Senhas em cadastro e troca devem ser checadas contra senhas vazadas (6.2.12, L2). O reset de senha não pode contornar o MFA (6.4.3, L2). E-mail não pode ser fator de autenticação (6.3.6, L3). A documentação deve definir rate limiting e anti-automação contra credential stuffing (6.1.1) — [ASVS 5.0 – V6 Authentication](https://github.com/OWASP/ASVS/blob/master/5.0/en/0x15-V6-Authentication.md)
- Logs de segurança são distintos dos logs de erro. Eles "não devem incluir dados pessoais sensíveis salvo exigência legal" e devem ser protegidos como ativo de alto valor. É preciso ter um inventário de logging por camada (16.1.1) — [ASVS 5.0 – V16 Logging](https://github.com/OWASP/ASVS/blob/master/5.0/en/0x25-V16-Security-Logging-and-Error-Handling.md)

**Cloudflare (WAF, rate limiting, bots)**
- WAF Managed Rules por plano: o "Free Managed Ruleset" existe em todos os planos. O "Cloudflare Managed Ruleset" e o "Cloudflare OWASP Core Ruleset" exigem **Pro ou superior**. "Sensitive Data Detection" é exclusivo do Enterprise — [cloudflare-docs – WAF managed rules](https://github.com/cloudflare/cloudflare-docs/blob/production/src/content/docs/waf/managed-rules/index.mdx)
- Rate limiting rules por plano: **Free**, 1 regra, período de contagem de 10 s, contagem por IP, campos só Path e Verified Bot. **Pro**, 2 regras, até 1 min e mitigação de até 1 h. **Business**, 5 regras, até 10 min, contagem "IP with NAT support" e mitigação de até 1 dia. **Enterprise** depende do contrato ou do Advanced Rate Limiting — [cloudflare-docs – rate limiting availability by plan](https://github.com/cloudflare/cloudflare-docs/blob/production/src/content/partials/waf/rate-limiting-availability-by-plan.mdx)
- O "Bot Fight Mode" é gratuito e desafia requisições com padrão de bot nos planos Free, mas não aceita exceções. Para exceções (APIs próprias, monitoramento) usa-se o "Super Bot Fight Mode", que tem Skip rules. Ambos podem desafiar tráfego legítimo de API e de apps móveis — [cloudflare-docs – Bot Fight Mode](https://github.com/cloudflare/cloudflare-docs/blob/production/src/content/docs/bots/get-started/bot-fight-mode.mdx); [plan considerations](https://github.com/cloudflare/cloudflare-docs/blob/production/src/content/partials/bots/about-plan-considerations.mdx)
- O **Turnstile** (CAPTCHA invisível da Cloudflare) tem plano Free indicado para "most production applications". O Enterprise acrescenta detecção avançada e fingerprinting — [cloudflare-docs – Turnstile plans](https://github.com/cloudflare/cloudflare-docs/blob/production/src/content/docs/turnstile/plans.mdx)

**Sinal do mercado**
- A Eneba mantém vaga de "Backend Engineer, Security" para política de segurança entre times (via resumo de busca) — [Eneba – Lever (Security)](https://jobs.eu.lever.co/eneba/d12a7fe5-58e7-4039-9cc0-9b96bd97f9b8)

**Marco legal (fontes canônicas) [não verificado nesta sessão — planalto.gov.br inacessível]**
- LGPD (Lei 13.709/2018): art. 46, medidas de segurança técnicas e administrativas; art. 48, comunicação de incidente à ANPD e aos titulares; art. 41, encarregado (DPO) — [Lei 13.709/2018](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- Marco Civil da Internet (Lei 12.965/2014), art. 15: provedores de aplicação constituídos como pessoa jurídica devem guardar registros de acesso a aplicações por 6 meses, sob sigilo e em ambiente seguro — [Lei 12.965/2014](https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2014/lei/l12965.htm)

### Inferences
- **Arquitetura de segurança recomendada (inferência):**
  - **Borda:** Cloudflare Pro (Managed + OWASP rulesets; 2 regras de rate limit para `/login` e `/api/checkout`; Turnstile em cadastro, login, saque e reset; Super Bot Fight Mode). Subir para Business se precisar de mais regras de rate limit ou contagem com NAT, porque muitos usuários brasileiros saem por CGNAT de operadora móvel e a contagem pura por IP gera falsos positivos.
  - **Aplicação:** ASVS L2 como linha de base, com L3 seletivo: passkeys ou chave de hardware **obrigatórias** para admin e operadores de cofre (6.3.3 L3); senha + TOTP ou passkey para clientes; 2FA obrigatório para saque e alteração de chave Pix; verificação de senha vazada (6.2.12).
  - **Cofre de entrega:** envelope encryption com KMS (AWS KMS, GCP Cloud KMS ou OpenBao/Vault). A chave de dados é por item e o texto claro nunca é registrado em log. A revelação é feita por endpoint dedicado com step-up auth, gera registro imutável e torna o item "revelado" (não reutilizável). Admins veem apenas metadados, nunca o segredo, salvo via fluxo de 4-olhos auditado.
  - **Segredos de infraestrutura:** gerenciador de segredos do provedor (AWS Secrets Manager, GCP Secret Manager ou o gerenciador nativo do PaaS), rotação de chaves de PSP e webhooks, nenhum segredo no repositório (secret scanning no CI).
  - **Backups:** PITR do Postgres, cópia diária cifrada em outra conta ou região e teste de restauração mensal. O cofre exige que a chave KMS também tenha plano de recuperação.
  - **Logs e monitoramento:** logs de segurança separados (ASVS V16), sem dados pessoais sensíveis; retenção de logs de acesso de no mínimo 6 meses (Marco Civil art. 15); alertas para picos de login falho, chargebacks, revelações de cofre fora do padrão e saques.
  - **LGPD:** inventário de dados, base legal por finalidade, DPO, plano de resposta a incidentes, minimização (não guardar documentos de KYC além do necessário), criptografia em repouso de CPF e chave Pix.
- O ASVS é verificável: contratar um pentest com escopo "ASVS L2 + cofre/carteira L3" antes da abertura a terceiros é um diferencial que pode ser comunicado ao mercado.

### Gaps
- Preços mensais atuais dos planos Cloudflare Pro e Business: cloudflare.com inacessível. Os docs no GitHub não trazem preço.
- Prazo regulamentar de comunicação de incidente à ANPD (Regulamento de Comunicação de Incidente) e regras para agentes de pequeno porte: não verificado nesta sessão (ver as notas jurídicas de outro pesquisador).
- Requisitos específicos do ASVS para passkeys/WebAuthn (seção V6.5 em diante) não foram extraídos em detalhe.

## 5. Hospedagem e custos (MVP vs. escala; latência Brasil) e serviços de terceiros

### Takeaway
Para latência baixa no Brasil, priorizar provedores **com região em São Paulo**: Supabase (AWS `sa-east-1`), Fly.io (`gru`) e GCP (`southamerica-east1`). A AWS `sa-east-1` também existe, mas não foi verificada aqui. **Railway não tem região no Brasil** (só EUA, Amsterdã e Singapura). Um MVP enxuto custa na ordem de **US$ 50–150/mês** em infraestrutura (Supabase Pro + 2 máquinas pequenas Fly.io em `gru` + Cloudflare Pro), mais e-mail e WhatsApp por uso. Esse valor é estimativa a partir dos preços citados abaixo.

### Cited Findings
**Supabase**
- Planos Free, Pro, Team e Enterprise. **Pro = US$ 25/mês**, com **US$ 10/mês de Compute Credits**, que cobrem um projeto em Micro/Nano — [Supabase – your monthly invoice](https://github.com/supabase/supabase/blob/master/apps/docs/content/guides/platform/your-monthly-invoice.mdx); [Supabase – compute usage](https://github.com/supabase/supabase/blob/master/apps/docs/content/guides/platform/manage-your-usage/compute.mdx)
- Tamanhos de compute (USD/mês aprox.): Micro ~10 (1 GB RAM), Small ~15 (2 GB), Medium ~60 (4 GB), Large ~110 (2 vCPU dedicadas, 8 GB), XL ~210 (4 vCPU, 16 GB) — [Supabase compute-and-disk](https://github.com/supabase/supabase/blob/master/apps/docs/content/guides/platform/compute-and-disk.mdx)
- A região "South America (São Paulo)" (`sa-east-1`) está na lista de regiões AWS do Supabase. A região escolhida determina onde os dados primários ficam armazenados, mas "seleção de região é controle de localização, não prova de conformidade" — [Supabase regions.ts](https://github.com/supabase/supabase/blob/master/packages/shared-data/regions.ts); [Supabase – Available regions](https://github.com/supabase/supabase/blob/master/apps/docs/content/guides/platform/regions.mdx)

**Fly.io**
- Sem taxa de plataforma, cobrança por uso. `shared-cpu-1x` 256 MB: US$ 2,19/mês; 512 MB: US$ 3,69; 1 GB: US$ 6,70; `shared-cpu-2x` 2 GB: US$ 13,39; `performance-1x` 2 GB: US$ 33; `performance-2x` 4 GB: US$ 66 — [Fly.io pricing (docs no GitHub)](https://github.com/superfly/docs/blob/main/about/pricing.mdx)
- Saída para a internet: **US$ 0,04/GB na América do Sul** (US$ 0,02/GB na América do Norte e Europa). Volume: US$ 0,15/GB/mês. Managed Postgres de US$ 38/mês (Basic) a US$ 1.922/mês (Performance). Suporte Standard US$ 29/mês. O exemplo oficial "app pequeno + Managed Postgres" custa US$ 43,67/mês — [Fly.io pricing](https://github.com/superfly/docs/blob/main/about/pricing.mdx)
- O preço da máquina varia por região: a mesma `shared-cpu-1x` 1 GB custa US$ 6,70 em `iad`, US$ 7,73 em `fra` e US$ 8,50 em `sin` — [Fly.io pricing](https://github.com/superfly/docs/blob/main/about/pricing.mdx)
- A região `gru` (São Paulo, Brasil) consta na lista de regiões da Fly.io — [Fly.io regions](https://github.com/superfly/docs/blob/main/reference/regions.mdx)

**Railway**
- Planos: Free US$ 0 (US$ 1 de crédito por mês), Hobby US$ 5/mês (inclui US$ 5 de uso) e Pro US$ 20/mês (inclui US$ 20 de uso). RAM US$ 10/GB/mês, CPU US$ 20/vCPU/mês, egress US$ 0,05/GB e volume US$ 0,15/GB/mês — [Railway pricing plans](https://github.com/railwayapp/docs/blob/main/content/docs/pricing/plans.md)
- Regiões disponíveis: US West (Califórnia), US East (Virgínia), EU West (Amsterdã) e Southeast Asia (Singapura). **Não há região no Brasil** — [Railway regions](https://github.com/railwayapp/docs/blob/main/content/docs/deployments/regions.md)

**Google Cloud**
- No Cloud Run, `southamerica-east1` (São Paulo) é cobrada no **Tier 2**, mais caro que o Tier 1 de `us-central1`, `us-east1` etc. — [Cloud Run pricing](https://cloud.google.com/run/pricing)
- Cloud Run, faturamento por requisição: o free tier mensal inclui 180.000 vCPU-s, 360.000 GiB-s e 2 milhões de requisições (base us-central1). Tier 1: US$ 0,000024 por vCPU-s ativo e US$ 0,0000025 por GiB-s. No faturamento por instância, o free tier é de 240.000 vCPU-s e 450.000 GiB-s, com Tier 1 a US$ 0,000018 por vCPU-s e US$ 0,000002 por GiB-s. Os valores do Tier 2 não foram extraídos — [Cloud Run pricing](https://cloud.google.com/run/pricing)
- O Cloud SQL lista São Paulo (`southamerica-east1`) entre as regiões com preço — [Cloud SQL pricing](https://cloud.google.com/sql/pricing)

### Inferences
- **Estimativas de custo (inferência, a partir dos preços acima; câmbio e impostos não incluídos):**

| Cenário | Composição | Ordem de grandeza (US$/mês) |
|---|---|---|
| **MVP (2 vendedores, até ~10 mil visitas/dia)** | Supabase Pro (US$ 25, Micro coberto pelos créditos; Small ≈ +US$ 5) em `sa-east-1` + 2× Fly.io `shared-cpu-1x` 1 GB em `gru` (~US$ 7–9 cada; o preço em `gru` não foi verificado) + 1 worker 512 MB (~US$ 4) + egress 50 GB × US$ 0,04 (US$ 2) + Cloudflare Pro (preço não verificado) + e-mail transacional + domínio | **~50–150** |
| **MVP alternativo (sem BaaS)** | Fly.io `gru` (app + worker) + Fly Managed Postgres Basic (US$ 38) + Redis gerenciado | **~70–150** |
| **Marketplace inicial (F2)** | Supabase Medium/Large (US$ 60–110) ou Postgres gerenciado equivalente + 3–4 máquinas `performance-1x` (US$ 33 cada) + Centrifugo/Redis + busca (Meilisearch ou Typesense) + Cloudflare Business + monitoramento/SIEM | **~400–1.200** |
| **Escala (dezenas de milhares de pedidos/mês)** | AWS `sa-east-1` ou GCP `southamerica-east1` com Kubernetes ou Cloud Run, Postgres HA com réplicas, KMS, WAF Enterprise/Bot Management | **US$ 3.000+**, dominado por banco HA, WAF e observabilidade |

- **Railway** é barato e simples, mas, sem região no Brasil, toda requisição dinâmica atravessa o continente. Serve para staging e para workers sem requisito de latência, não para a API de checkout e chat.
- **Vercel** para o frontend Next.js é plausível com o Cloudflare na frente, mas os preços não foram verificados nesta sessão. Hospedar o Next.js na própria Fly.io `gru` ou no Cloud Run `southamerica-east1` mantém o SSR perto do usuário e evita custos de egress em dois provedores.
- Manter os dados primários em São Paulo (`sa-east-1`) simplifica a narrativa de LGPD. Mesmo assim, transferência internacional é permitida com salvaguardas, e a região "não é prova de conformidade" (Supabase).
- Usar um BaaS como o Supabase no MVP acelera autenticação, storage e realtime. Mas o cofre e a carteira **não** devem depender só de RLS no cliente: a lógica sensível fica em serviço backend próprio com chaves no KMS.

### Gaps
- Preços atuais de **Vercel** (Pro, uso de functions e banda), **AWS** (`sa-east-1`: EC2, RDS, KMS, Secrets Manager), **Cloudflare Pro/Business**, valores Tier 2 do Cloud Run e Cloud SQL em São Paulo: páginas inacessíveis ou dinâmicas.
- Preço da máquina Fly.io especificamente em `gru` e o significado da coluna marcada (✓) na tabela de regiões.
- **WhatsApp Business Platform**: o modelo atual (cobrança por mensagem por categoria de template), os valores para o Brasil e as janelas gratuitas de atendimento não foram verificados (developers.facebook.com inacessível).
- E-mail transacional (Resend, Amazon SES, Postmark, SendGrid) e chat gerenciado (Pusher, Ably, Stream): preços não verificados.
- Latência medida (ms) São Paulo ↔ Virgínia/Califórnia: nenhuma fonte obtida.

## 6. Ferramentas de clonagem/referência de sites e limites legais da cópia

### Takeaway
Há ferramentas maduras para **analisar** um site de referência: Firecrawl (+ MCP), Playwright MCP, Chrome DevTools MCP e Crawl4AI. Para **gerar código a partir de telas** existe o screenshot-to-code. Nesta sessão do Claude Code também foi instalado o pacote de skills **"Replica"** (recon → arquitetura → design → build → brand → diff). O limite jurídico prático: ideias, funcionalidades e fluxos podem ser reproduzidos. **Código, textos, imagens, ícones, logotipo, marca e o "conjunto-imagem" (trade dress) não podem.** A screenshot-to-code pode "reaproveitar logos e imagens reais da captura", exatamente o que deve ser desligado ou descartado.

### Cited Findings
**Ferramentas**
- **Firecrawl**: cerca de 190,6 mil estrelas, licença principal AGPL-3.0 (SDKs e alguns componentes de UI em MIT) — [GitHub firecrawl/firecrawl](https://github.com/firecrawl/firecrawl)
- **Firecrawl MCP Server**: ferramentas `firecrawl_scrape` (URL → markdown/JSON com schema), `firecrawl_map` (descobrir URLs), `firecrawl_crawl` (várias páginas com `limit`, `includePaths`, `maxDiscoveryDepth`), `firecrawl_search`, `firecrawl_interact` (clicar e digitar antes de ler) e `firecrawl_monitor_*` (diffs recorrentes). O MCP hospedado (`https://mcp.firecrawl.dev/v2/mcp`) tem um free tier sem chave para `scrape`, `search` e `parse` com limite de taxa; `crawl`, `map` e `agent` exigem chave — [GitHub firecrawl/firecrawl-mcp-server](https://github.com/firecrawl/firecrawl-mcp-server)
- **Playwright MCP** (Microsoft): cerca de 38,0 mil estrelas, Apache-2.0. Opera por "accessibility snapshots" estruturados, sem modelo de visão, e instala com `claude mcp add playwright npx @playwright/mcp@latest`. Capacidades opcionais: `vision`, `pdf` e `devtools` — [GitHub microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp)
- **Chrome DevTools MCP** (`chrome-devtools-mcp`): permite a agentes como o Claude controlar e inspecionar um Chrome real, com traces de performance, análise de rede, screenshots e console — [GitHub ChromeDevTools/chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp)
- **Crawl4AI**: crawler open-source que converte sites em Markdown "LLM-ready", para rodar localmente ou hospedado — [GitHub unclecode/crawl4ai](https://github.com/unclecode/crawl4ai)
- **screenshot-to-code**: cerca de 80,2 mil estrelas, MIT. Converte screenshots, mockups, Figma e **gravações de tela** em código (HTML+Tailwind, HTML+CSS, React+Tailwind, Vue+Tailwind, Bootstrap, Ionic). Frontend React/Vite e backend FastAPI; exige chave OpenAI, Anthropic ou Gemini. O Gemini "faz extração de assets (reutilizando os logos/imagens reais da sua captura)" — [GitHub abi/screenshot-to-code](https://github.com/abi/screenshot-to-code)
- **Pacote "Replica" instalado nesta sessão** (skills `replica-recon`, `-architect`, `-design`, `-build`, `-backend`, `-brand`, `-diff`, `-test`, `-deploy`, `-launch`, `-entrepreneur`). Regras embutidas:
  - recon "só de fontes públicas e da conta do próprio usuário"; nunca entrar em conta alheia nem "descompilar bundles JavaScript ou registrar chamadas de rede para copiar" — `/root/.claude/skills/replica-recon/SKILL.md`
  - build "escreve cada linha do zero, nunca o código, assets ou textos do original"; "nunca colar HTML, CSS, JS, SVGs ou imagens do original, nunca carregar nada do domínio/CDN dele"; "Igualar o que um botão faz é paridade. Igualar a frase dele é cópia." — `/root/.claude/skills/replica-build/SKILL.md`
  - design: nunca usar logos, ícones, ilustrações, fotos ou sons do alvo; textos reescritos; "o layout assinatura é trade dress, e muda antes do lançamento" — `/root/.claude/skills/replica-design/SKILL.md`
  - brand: buscas de marca são "triagem, não liberação jurídica", e "um advogado de marcas deve fazer a busca". A tabela de bases cita EUA, UE, Canadá e WIPO Global Brand Database, **mas não o INPI** — `/root/.claude/skills/replica-brand/SKILL.md`

**Limites legais no Brasil (fontes canônicas) [não verificado nesta sessão — planalto.gov.br inacessível]**
- Lei de Direitos Autorais (9.610/1998): protege "obras intelectuais... expressas por qualquer meio" (art. 7º), incluindo textos, fotografias, desenhos e ilustrações. O art. 8º, I exclui da proteção "as ideias, procedimentos normativos, sistemas, métodos, projetos ou conceitos matemáticos como tais" — [Lei 9.610/1998](https://www.planalto.gov.br/ccivil_03/leis/l9610.htm)
- Programas de computador têm proteção própria de direito autoral (Lei 9.609/1998). Copiar o código-fonte ou o JavaScript do site alvo viola essa lei — [Lei 9.609/1998](https://www.planalto.gov.br/ccivil_03/leis/l9609.htm)
- Lei de Propriedade Industrial (9.279/1996): o art. 195, III tipifica como crime de concorrência desleal "emprega[r] meio fraudulento, para desviar, em proveito próprio ou alheio, clientela de outrem". O art. 209 garante indenização por atos de concorrência desleal "tendentes a... criar confusão entre estabelecimentos... ou entre os produtos e serviços postos no comércio". É a base usual da proteção de **trade dress** (conjunto-imagem) no Brasil, que não tem artigo específico — [Lei 9.279/1996](https://www.planalto.gov.br/ccivil_03/leis/l9279.htm)

### Inferences
- **Uso seguro das ferramentas (inferência):**
  1. **Análise**: Firecrawl `map` e `scrape` ou Crawl4AI para inventariar páginas, categorias, campos de anúncio, FAQ e regras públicas (prazos, taxas). Playwright ou Chrome DevTools MCP para capturar fluxos e estados de tela como **referência interna**. Respeitar os termos de uso e o robots.txt do alvo, e não automatizar login nem raspar dados pessoais de vendedores (LGPD).
  2. **Especificação**: transformar as capturas em **matriz de funcionalidades e fluxos** (o que é ideia/método, não protegido), não em HTML.
  3. **Design próprio**: novo design system (cores, tipografia, ícones open-source, ilustrações próprias), copy própria e nome e logo próprios. Busca de anterioridade no **INPI** (ausente no pacote Replica) antes de registrar a marca.
  4. **screenshot-to-code**: útil para prototipar **a partir dos wireframes próprios**. Se usado sobre capturas do GGMax, desativar a extração de assets e substituir todo texto e imagem antes de qualquer commit.
- **Riscos concretos de "parecer demais com o GGMax":** layout assinatura + paleta + nomes de planos (ex.: "Prata/Ouro/Diamante") + textos de FAQ copiados podem configurar confusão (LPI art. 209) e violação de direito autoral sobre os textos (Lei 9.610). A funcionalidade (escrow, chat por pedido, prazos de liberação por categoria, planos de comissão) é livre.
- O Firecrawl é AGPL-3.0: usar o serviço hospedado ou o MCP para análise não "contamina" o código do site, mas embutir o código-fonte do Firecrawl num serviço próprio modificado traria obrigações AGPL.

### Gaps
- Jurisprudência recente (STJ/TJSP) sobre trade dress de **sites e apps** e sobre cópia de layout: não pesquisada por falta de orçamento de busca (cobrir nas notas jurídicas).
- Termos de uso do GGMax sobre scraping e uso de conteúdo: não lidos (site inacessível).
- Ferramentas "website-to-code cloners" comerciais (ex.: serviços que exportam HTML de qualquer URL) e seus termos: não pesquisados.

## 7. Roadmap faseado (MVP de 2 vendedores → marketplace) com estimativas de esforço

### Takeaway
Um roadmap em 3 fases: **F0 (fundação, 2–3 semanas)**, **F1 (MVP loja própria com cofre, carteira simples, chat e disputas, ~10–16 semanas)** e **F2 (marketplace aberto com KYC, escrow por vendedor, reputação e planos de comissão, ~12–20 semanas adicionais)**. Isso vale para um time de 2–3 desenvolvedores full-stack mais apoio de design e segurança. As estimativas são **inferência do autor**, não vêm de fonte externa.

### Cited Findings
- Referência de regra de negócio a reproduzir (com outros números) na F2: comissão por plano de 9,99% a 12,99%, liberação em 4/7 dias reduzida pela metade com avaliação positiva, análise de até 180 dias — [Termos de uso GGMax](https://www.ggmax.com.br/termos-de-uso); [Tarifas e prazos GGMax](https://ggmax.com.br/tarifas-e-prazos); [calculadora-de-taxas-ggmax](https://github.com/muriloatavares/calculadora-de-taxas-ggmax)
- Atalho para a F2 em motor headless: plugin de exemplo multivendor no Vendure com `platformFeePercent` e registro de vendedor, e receita de Marketplace Module no Medusa — [Vendure multivendor-plugin](https://github.com/vendure-ecommerce/vendure/blob/master/packages/dev-server/example-plugins/multivendor-plugin/README.md); [Medusa Marketplace Recipe](https://github.com/medusajs/medusa/blob/develop/www/apps/resources/app/recipes/marketplace/page.mdx)
- Meta de segurança por fase: ASVS L2 (cerca de 70% dos requisitos, MFA obrigatório) — [ASVS 5.0 – What is the ASVS](https://github.com/OWASP/ASVS/blob/master/5.0/en/0x03-What-is-the-ASVS.md); [ASVS V6](https://github.com/OWASP/ASVS/blob/master/5.0/en/0x15-V6-Authentication.md)
- Escala de referência no topo do mercado: Eneba com mais de 100 microsserviços e mais de 50 deploys por dia (via resumo de busca) — [Eneba – Lever](https://jobs.eu.lever.co/eneba/7e8ef892-36b8-4a2d-970b-d19e136a581c)

### Inferences
**Stack recomendada (inferência):**
- **Frontend**: Next.js (App Router) com SSR/ISR para páginas SEO de jogo e categoria; Tailwind + biblioteca de componentes própria.
- **Backend**: NestJS (ou Node/Fastify) modular em monólito (catálogo, pedidos, pagamentos, cofre, carteira, chat, disputas, admin), com fila e jobs (BullMQ/Redis ou pg-boss) para liberação de escrow, webhooks e notificações. Opcionalmente, Medusa como núcleo de catálogo e checkout.
- **Dados**: PostgreSQL (ledger de partidas dobradas, máquina de estados, auditoria append-only) + Redis (sessões, rate limit da aplicação, filas) + storage S3-compatível para anexos.
- **Tempo real**: Centrifugo (ou Socket.IO) com Redis; no Supabase, o Realtime pode servir no MVP.
- **Autenticação**: Better Auth (TOTP + passkeys) ou provedor gerenciado; step-up para revelação de cofre e saque.
- **Segurança**: Cloudflare Pro + Turnstile; KMS para o cofre; Secret Manager; Sentry + logs estruturados + alertas.
- **Hospedagem**: São Paulo (Supabase `sa-east-1` + Fly.io `gru`, ou GCP `southamerica-east1`).
- **Monólito modular primeiro**: microsserviços só depois de gargalos reais (o caso Eneba é ponto de chegada, não de partida).

**Fases e esforço (inferência; time de 2–3 devs full-stack + 1 designer parcial + consultoria de segurança):**

| Fase | Escopo | Esforço estimado |
|---|---|---|
| **F0 – Fundação** | Repositório, CI/CD, IaC básica, ambientes (dev/staging/prod em SP), Cloudflare, autenticação com 2FA e passkeys, RBAC admin, logging, backups, design system próprio | 2–3 semanas |
| **F1 – MVP loja própria (2 vendedores)** | Catálogo por jogo e categoria com variações; busca Postgres; carrinho e checkout; PSP com Pix e cartão e webhooks idempotentes; máquina de estados do pedido; **cofre de entrega automática** (KMS, revelação única, auditoria); entrega manual assistida para contas e serviços via chat; **chat por pedido** (comprador ↔ loja); avaliações da loja; tickets e disputas; carteira simples (saldo e reembolso em crédito); cupons; e-mail + WhatsApp transacional; páginas SEO; painel admin; LGPD (política, consentimento, DPO); pentest focado | 10–16 semanas |
| **F1.5 – Endurecimento** | Antifraude (velocity rules, lista de bloqueio, score de chargeback), Turnstile em pontos críticos, monitoramento de revelações, testes de carga, ASVS L2 checklist completo | 3–4 semanas |
| **F2 – Marketplace aberto** | Cadastro e KYC de vendedores; planos de comissão; anúncios de terceiros com moderação; **escrow por vendedor** (liberação agendada por categoria, bloqueio em disputa); saque Pix com 2FA e antifraude; split no PSP (se disponível) ou ledger interno + repasse; reputação por vendedor; chat comprador ↔ vendedor com filtros anti-evasão; mediação de disputas; afiliados; busca dedicada (Meilisearch ou Typesense); notificações push | 12–20 semanas |
| **F3 – Escala** | Réplicas de leitura, CDN de imagens, filas dedicadas, separação de serviços críticos (pagamentos, cofre), SIEM, bug bounty, app mobile/PWA | Contínuo |

- **Decisão de arquitetura que evita reescrita**: modelar **desde o MVP** as tabelas `sellers` (com os 2 sócios como vendedores), `ledger_entries`, `escrow_holds` e `order_events`, mesmo com regras simples. Abrir para terceiros vira então um problema de onboarding e políticas, não de esquema de dados.
- **Custo de pessoas domina**: com infraestrutura de MVP de ~US$ 50–150/mês, o custo real está no desenvolvimento (cerca de 6–9 meses-pessoa até o fim da F1.5 e +6–10 até a F2, pelas estimativas acima) e na operação (suporte, mediação, antifraude).

### Gaps
- Não encontrei benchmarks públicos de esforço ou custo de construção de marketplaces gamer no Brasil. O orçamento do projeto Workana "inspirado em ggmax" não pôde ser lido.
- Taxas e capacidades de split/custódia dos PSPs brasileiros (o que define se a F2 usa split nativo ou ledger interno + repasse) não foram verificadas.
- Custos de KYC (provedores brasileiros de verificação de documento e selfie) e de antifraude: não pesquisados.
