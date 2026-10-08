# Segurança, privacidade e uso responsável

## Credenciais e segredos

- Chaves de providers de IA existem **só no servidor** (API e worker). O provider declara
  em `providers.yaml` apenas os **nomes** das variáveis (`credentials_env`); o adapter lê o
  valor com `self.credential(...)`, que recusa nomes não declarados. Sem a credencial, o
  provider fica indisponível no roteador com o motivo visível em `GET /providers`.
- O frontend recebe uma única configuração, `NEXT_PUBLIC_API_URL`. Nenhuma chamada a
  provider sai do navegador.
- Configurações sensíveis são `SecretStr`: não aparecem em logs, reprs nem respostas.
- `.env`, `.env.local` e similares estão no `.gitignore`; só os `.env.example` (sem
  valores reais) são versionados.
- Com `APP_ENV=production` a API **não sobe** se `JWT_SECRET` ou `SIGNING_SECRET` estiverem
  no valor padrão, ou se `AUTH_DEV_AUTOLOGIN` estiver ligado.

## Autenticação e isolamento

- Senhas com scrypt (stdlib, salt aleatório); tokens JWT com expiração
  (`JWT_TTL_MINUTES`).
- Todo acesso a projeto passa por `get_owned_project`: o projeto de outro usuário responde
  **404**, indistinguível de um inexistente (não vaza a existência).
- Rotas administrativas (`/admin/*`) exigem `is_admin`.
- Em desenvolvimento, `AUTH_DEV_AUTOLOGIN` faz requisições sem token agirem como o usuário
  dev — conveniência local, proibida em produção.

## Superfície da API

- Rate limit por usuário em janela fixa (Redis quando disponível, memória caso contrário),
  com limite separado e mais baixo para rotas caras (`RATE_LIMIT_EXPENSIVE_PER_MINUTE`:
  início de upload, análise, preview de frame e geração).
- Erros sempre no formato `{"error": {code, message, details, requestId}}`; exceções não
  tratadas viram `INTERNAL_ERROR` genérico, com o detalhe só no log (correlacionado pelo
  `X-Request-Id`). Mensagens brutas de providers nunca chegam ao cliente.
- CORS restrito a `CORS_ORIGINS`.
- Operações caras exigem plano confirmado e aceitam `Idempotency-Key`: um clique duplo
  ou um retry de rede não dispara duas gerações.

## Mídia

- **Validação em duas etapas:** no início do upload (tipo declarado, tamanho, confirmação
  de direitos) e depois do upload, pelo conteúdo real com ffprobe — contêiner, codec,
  duração mínima/máxima, presença de vídeo. A extensão do arquivo não é confiável e não é
  usada para decidir nada.
- Uploads e downloads usam **URLs assinadas com expiração** (`SIGNED_URL_TTL_SEC`): presign
  do S3/MinIO, ou HMAC-SHA256 com `SIGNING_SECRET` no storage local (comparação em tempo
  constante). O bucket não precisa ser público.
- Chaves de storage são prefixadas por projeto (`projects/<id>/…`), o que permite apagar
  toda a mídia de um projeto de uma vez.
- O FFmpeg roda com argumentos em lista (sem shell) e com timeout (`FFMPEG_TIMEOUT_SEC`).

## Direitos sobre o vídeo

- O upload só é aceito com `rightsConfirmed: true`. O texto da declaração e a data da
  confirmação ficam gravados no `source_videos`:
  > Declaro que sou o autor deste vídeo, que possuo licença para utilizá-lo ou que tenho
  > autorização expressa dos titulares para transformá-lo. Entendo que alterações feitas
  > pela ferramenta não tornam o conteúdo automaticamente livre de direitos autorais.
- Texto na tela (legendas, placas, logos) é detectado mas **nunca alterado
  automaticamente** (`autoModify: false`); só muda se o usuário pedir.

## Privacidade e retenção

- `MEDIA_RETENTION_DAYS` define a data de expiração da mídia de cada vídeo enviado;
  `uv run videodna cleanup-media` apaga o que venceu (agende como cron em produção).
- O usuário pode excluir o projeto inteiro (`DELETE /projects/{id}`) ou só a mídia
  (`DELETE /projects/{id}/media`), mantendo o histórico sem os arquivos.
- O log de requisições registra método, rota, status, latência e IDs — nunca corpo de
  requisição, conteúdo de vídeo ou credenciais.
- Antes de ligar um provider real, a ficha de pesquisa em [providers.md](providers.md)
  pede a política de retenção e de uso para treino daquele fornecedor: o usuário envia
  vídeos com pessoas, e essa informação precisa estar clara antes de enviar qualquer frame.

## Proveniência e transparência

- Todo resultado gerado leva um **provenance JSON** em `generation_outputs.provenance`:
  vídeo e hash de origem, análise, plano, modo de qualidade, locks, operações aplicadas,
  providers e tentativas por shot, se foi mock, data.
- Na montagem os metadados do contêiner de origem são descartados (`-map_metadata -1`),
  para não carregar informações do arquivo original (dispositivo, localização) para o
  resultado.
- O selo "MOCK MODE" aparece na interface sempre que os resultados são simulados.

## Uso responsável

O VideoDNA Studio é uma ferramenta de edição criativa sobre conteúdo do próprio usuário.
Por decisão de projeto, **não** implementa nada cuja finalidade seja enganar sistemas de
autoria, de fingerprint de conteúdo ou de detecção de mídia gerada por IA — nem remover
marcas d'água ou sinais de proveniência que providers venham a incluir nos resultados.
Novos recursos com esse objetivo não devem ser aceitos.
