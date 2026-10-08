# Providers de IA

Nenhuma parte do produto conhece um fornecedor de IA. O código de negócio pede uma
**capability** ao orquestrador; o roteador escolhe, entre os providers registrados e
disponíveis, o que melhor atende ao modo de qualidade; o adapter traduz a chamada para a
API daquele fornecedor. Trocar de fornecedor é escrever um adapter e uma entrada no
registro.

> **Regra do projeto:** endpoint, parâmetro, modelo, limite e preço de um provider real
> vêm **da documentação oficial dele**, consultada na hora de escrever o adapter, com a URL
> e a data registradas. Nada é estimado, lembrado ou copiado de terceiros. Os valores dos
> providers mock em `providers.yaml` são fictícios e estão marcados como tal.

## Capabilities e tipos

| Tipo (`kind`) | Interface | Capabilities |
|---------------|-----------|--------------|
| `video_analyzer` | `VideoAnalyzerProvider.analyze_video` | `video.understanding` |
| `image_analyzer` | `ImageAnalyzerProvider.analyze_images` | `object.detection`, `object.grounding`, `ocr` |
| `segmentation` | `SegmentationProvider.segment` | `segmentation.image`, `segmentation.video` |
| `tracking` | `TrackingProvider.track` | `tracking.multi_object` |
| `speech` | `SpeechProvider.transcribe` | `speech.transcription` |
| `suggestion` | `SuggestionProvider.suggest` | `text.suggestions` |
| `image_generator` | `generate_image`, `edit_image` | `image.generate`, `image.edit` |
| `video_editor` | `VideoEditorProvider.edit_video` | `video.attribute_edit`, `video.localized_edit`, `video.background_replace`, `video.shot_reconstruction` |
| `video_generator` | `VideoGeneratorProvider.generate_video` | `video.shot_reconstruction`, `video.full_generation` |
| `qa` | `QAProvider.inspect` | `qa.video_inspection`, `qa.technical` |

Interfaces e modelos de request/response: `apps/api/src/videodna/orchestrator/interfaces.py`.
O carregamento do registro recusa um provider que declare uma capability que o seu tipo
não pode servir.

**Recursos** (`features`) que o planejador exige conforme os locks e a edição:
`mask_input`, `reference_images`, `motion_preservation`, `camera_preservation`,
`partial_range` (regenerar só uma janela do shot — usado no reparo localizado),
`chunking` (o runner divide shots maiores que o limite de duração).

## Registro (`apps/api/config/providers.yaml`)

```yaml
- name: mock-edit-pro                     # identificador único
  kind: video_editor
  adapter: videodna.orchestrator.adapters.mock.video:MockVideoEditor
  description: Edição localizada com máscara, tracking e referências.
  mock: true                              # só roda com AI_MOCK_MODE=true
  capabilities: [video.attribute_edit, video.localized_edit, video.background_replace]
  features: [mask_input, partial_range, reference_images, motion_preservation, camera_preservation, chunking]
  quality: {video.localized_edit: 0.84, default: 0.8}     # 0..1, por capability
  cost: {unit: second, amount: "0.90", per_call: "0.20", currency: BRL}
  limits: {max_duration_sec: 20, max_resolution_height: 1080}
  latency: {base_sec: 8, per_unit_sec: 3}
  prior_success_rate: 0.9
  models: [{id: mock-edit-pro-v2, default: true}]
```

| Campo | Significado |
|-------|-------------|
| `mock` / `local` | mock: só com `AI_MOCK_MODE=true`. local: roda na nossa infra (FFmpeg) e vale nos dois modos |
| `enabled`, `requires_flag` | desliga o provider ou o condiciona a uma feature flag; `provider.<name>=false` em `FEATURE_FLAGS` também desliga |
| `priority` | desempate |
| `quality` | nota 0..1 por capability (`default` para as demais) — deve vir dos *seus* testes de avaliação, não de marketing |
| `cost` | `unit` (`second`, `minute`, `image`, `call`, `1k_tokens`, `credit`), `amount`, `per_call`, `minimum`, `currency`, `resolution_multipliers` |
| `cost_by_capability` | custo diferente por capability |
| `limits` | duração máxima por chamada, resolução, imagens, concorrência, timeout |
| `latency` | estimativa para o plano (`base_sec + per_unit_sec × unidades`) |
| `prior_success_rate` | taxa de sucesso assumida até haver histórico próprio |
| `models` | modelos disponíveis; o `default` é usado quando a tarefa não pede outro |
| `docs_url` | **obrigatório** para provider real: de onde vieram limites e preços |
| `credentials_env` | **nomes** das variáveis de ambiente com as credenciais (nunca os valores) |
| `params` | parâmetros específicos do adapter |

## Roteamento

`AIProviderRouter.route(task)` recebe capability, modo de qualidade, duração, resolução,
recursos exigidos e exclusões, e devolve o escolhido **com a justificativa** e o ranking —
é o que a tela de revisão mostra em cada shot.

1. **Filtra** por disponibilidade: habilitado, modo mock × real, feature flags,
   credenciais presentes, saúde (`health_check` com cache), recursos exigidos, limites de
   resolução e duração (ou `chunking`), número de edições por chamada.
2. **Pontua** cada candidato com os pesos do modo:

   | Modo | custo | qualidade | sucesso | latência | piso de qualidade |
   |------|------:|----------:|--------:|---------:|------------------:|
   | `ECONOMY` | 0.55 | 0.20 | 0.20 | 0.05 | — |
   | `BALANCED` | 0.30 | 0.40 | 0.20 | 0.10 | 0.70 |
   | `MAX` | 0.02 | 0.70 | 0.25 | 0.03 | 0.80 |

   - custo = **custo efetivo** (preço ÷ taxa de sucesso), relativo ao mais barato — um
     provider barato que falha muito não é barato;
   - taxa de sucesso = prior combinado com o histórico real em `provider_usage`
     (o prior vale ~20 observações; abaixo de 50% observado há penalidade);
   - abaixo do piso de qualidade do modo: −0.3 (ainda usável se nada atinge o piso);
   - saúde degradada: −0.15.
3. **Executa** pelo gateway (`AIOrchestrator.run`): timeout, até `PROVIDER_MAX_ATTEMPTS`
   tentativas com backoff exponencial para erros transitórios, `ProviderUsage` gravado a
   cada tentativa e `CostEntry(ACTUAL)` no sucesso.
4. **Fallback** uma vez, para timeout, indisponibilidade, cota ou erro genérico: o roteador
   recalcula sem o provider que falhou e só aceita a alternativa se ela não custar mais que
   `FALLBACK_MAX_COST_INCREASE` acima da original. Conteúdo rejeitado e requisição inválida
   não caem para outro provider — o problema é o pedido, não o fornecedor.

Erros de SDK/HTTP são normalizados (`orchestrator/errors.py`) em `PROVIDER_TIMEOUT`,
`PROVIDER_QUOTA`, `PROVIDER_UNAVAILABLE`, `PROVIDER_INVALID_REQUEST`,
`PROVIDER_CONTENT_REJECTED` e `PROVIDER_ERROR`; o texto bruto do erro fica só nos logs.

### Custos

- Estimativa: `max(minimum, per_call + amount × quantidade × multiplicador de resolução)`.
- Preços em outra moeda são convertidos para `COST_CURRENCY` com as taxas de
  `FX_RATES_TO_BASE`, que **você** define (nada é assumido). Provider numa moeda sem taxa
  configurada fica indisponível para o roteador.
- Custo real: o adapter sobrescreve `actual_cost()` para ler o uso informado pelo provider
  (tokens, créditos, segundos); sem isso, vale o `reported_cost` ou a estimativa.
- Tudo vai para `cost_entries` (estimado × real, por projeto, job e shot) e aparece em
  `GET /projects/{id}/costs` e no painel admin.

## Adicionando um provider real — checklist

1. **Escolha pela capability**, não pelo fornecedor: qual etapa ele atende
   (`video.localized_edit`, `qa.video_inspection`…) e quais recursos ele precisa ter para os
   locks que importam (preservar câmera, movimento, aceitar máscara, referências…).
2. **Leia a documentação oficial** e preencha a ficha abaixo com links. Se algo não está
   documentado, registre "não documentado" — não estime.
3. **Implemente o adapter** em `orchestrator/adapters/<fornecedor>/`, herdando a interface
   do tipo. Regras:
   - leia credenciais com `self.credential("NOME_DA_VARIAVEL")` — só nomes declarados em
     `credentials_env` são aceitos;
   - traduza os erros com `normalize_exception` (ou lance `ProviderError` com o código
     certo) para que retry e fallback funcionem;
   - devolva `ProviderUsageInfo` com o uso real e sobrescreva `actual_cost()` se o
     fornecedor informar tokens/créditos;
   - implemente `health_check()` de forma barata (ou deixe o padrão);
   - nenhum dado do usuário em logs além do necessário; nada de credencial em mensagens.
4. **Registre** em `providers.yaml` com `mock: false`, `docs_url`, `credentials_env`,
   limites e preços da ficha, e `quality` vindo da sua avaliação. Use
   `requires_flag` para ligar gradualmente.
5. **Testes**: o teste de contrato
   (`test_every_registered_adapter_implements_its_interface`) já cobre interface e
   capabilities; acrescente testes do adapter com as respostas HTTP gravadas
   (sem chamar a API real na CI) e um teste de normalização de erros.
6. **Avalie** em vídeos de referência antes de aumentar `priority`: qualidade por
   capability, taxa de sucesso, latência e custo real × estimado.
7. Defina a credencial **só no ambiente do servidor/worker**. Nunca no frontend, nunca no
   repositório.

### Ficha de pesquisa (copiar para a PR do adapter)

| Item | Valor | Fonte (URL oficial) | Consultado em |
|------|-------|---------------------|---------------|
| Fornecedor / produto / modelo | | | |
| Capabilities que atende | | | |
| Autenticação (tipo, header) | | | |
| Endpoint(s) e modo (síncrono, job + polling, webhook) | | | |
| Entrada aceita (vídeo, imagem, máscara, referências, prompt) | | | |
| Duração máxima por chamada | | | |
| Resoluções / fps / formatos de saída | | | |
| Suporte a faixa parcial (regenerar trecho) | | | |
| Preservação de câmera / movimento | | | |
| Limites de taxa e concorrência | | | |
| Preço (unidade, moeda, mínimo, variação por resolução) | | | |
| Como o uso real é informado na resposta | | | |
| Retenção de dados enviados / uso para treino | | | |
| Políticas de conteúdo e direitos de imagem | | | |
| Marca d'água / metadados de proveniência no resultado | | | |
| Regiões / requisitos de LGPD | | | |

## Providers registrados hoje

Todos mock ou locais (`uv run videodna providers` lista com o estado de cada um):

| Provider | Tipo | Capabilities |
|----------|------|--------------|
| `mock-multimodal` | video_analyzer | video.understanding |
| `mock-detector` | image_analyzer | object.detection, object.grounding, ocr |
| `mock-segmenter` | segmentation | segmentation.image, segmentation.video |
| `mock-tracker` | tracking | tracking.multi_object |
| `mock-speech` | speech | speech.transcription |
| `mock-suggest` | suggestion | text.suggestions |
| `mock-imagegen` | image_generator | image.generate, image.edit |
| `mock-edit-lite` | video_editor | video.attribute_edit, video.localized_edit |
| `mock-edit-pro` | video_editor | video.attribute_edit, video.localized_edit, video.background_replace |
| `mock-v2v` | video_editor | video.background_replace, video.shot_reconstruction |
| `mock-gen` | video_generator | video.shot_reconstruction, video.full_generation |
| `mock-inspector` | qa | qa.video_inspection |
| `ffmpeg-qa` | qa (local) | qa.technical |

Os mocks têm perfis diferentes de custo, qualidade e recursos de propósito — "lite" barato
e limitado, "pro" com máscara e referências, "v2v" para cenário e reconstrução — para que
o roteador e o planejador tomem decisões reais em `AI_MOCK_MODE`.
