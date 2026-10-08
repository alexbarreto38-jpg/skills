# 0001 — Monólito modular com workers

- **Status:** Aceito
- **Data:** 2026-10-07

## Contexto

O produto tem uma parte interativa (editor, sugestões, impacto — respostas em
milissegundos) e uma parte pesada (FFmpeg, chamadas de IA que levam minutos). As duas
compartilham o mesmo modelo de domínio: o Video DNA, as operações, o plano. A equipe é
pequena e o domínio ainda está mudando.

## Decisão

Um único pacote Python, `videodna`, com módulos de fronteira clara e dependência numa só
direção (`api → services → domain`; `services → orchestrator | media | storage | jobs |
db`). O `domain/` não faz I/O. A mesma imagem Docker roda como API (`uvicorn`) ou como
worker (`videodna worker`); o trabalho pesado sempre passa por um job na fila.

## Alternativas consideradas

- **Microsserviços (análise, geração, edição separados)** — duplicaria o modelo do DNA ou
  exigiria um pacote compartilhado versionado, deploys coordenados e chamadas de rede onde
  hoje há chamadas de função, sem ganho enquanto o gargalo é o provider de IA, não a CPU
  da API.
- **Tudo síncrono na API** — análise e geração estourariam timeouts HTTP e prenderiam
  workers do servidor web.

## Consequências

- Refatorar o domínio é uma mudança local, testável sem rede.
- Escala-se a API e os workers de forma independente (réplicas do mesmo container com
  comandos diferentes).
- Se um módulo precisar sair (ex.: um serviço de geração em GPU própria), a fronteira já
  existe: o runner fala com o orquestrador por capability, não por import.
- Disciplina de imports é por convenção; um linter de arquitetura pode formalizá-la depois.
