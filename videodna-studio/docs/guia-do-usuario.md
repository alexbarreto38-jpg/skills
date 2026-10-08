# Guia do VideoDNA Studio

Este guia é para quem vai **usar** o VideoDNA Studio — não precisa saber programar. Ele
explica como instalar no Windows, como fazer a primeira edição e o que cada palavra da tela
quer dizer. Para desenvolvedores, o [README](../README.md) tem os detalhes técnicos.

<!-- screenshots:intro -->

## 1. O que o VideoDNA Studio faz

Você envia um vídeo e o programa o separa em partes que dá para mudar: as **cenas**, os
**personagens**, as **roupas**, os **objetos** e o **cenário**. Você clica numa parte e
escolhe como ela deve ficar — "cabelo cacheado", "camiseta azul", "copo → prato", "sala →
apartamento moderno". Antes de gerar, o programa mostra o que cada mudança afeta e quanto
custa. Depois gera o vídeo novo cena por cena, confere cada uma e mostra o antes e o depois.

O que não muda (a não ser que você peça): a história, a câmera, os movimentos das pessoas, o
som e a duração de cada cena.

### O que é simulado hoje (modo demonstração)

A IA de verdade ainda não está ligada. Enquanto isso o programa funciona em **modo
demonstração**, e o selo laranja "Modo demonstração" aparece no topo de todas as telas:

- os cortes, os quadros e as cores do vídeo **são medidos de verdade**;
- a análise por IA é **simulada**: ela sempre conta a mesma história de exemplo — um menino,
  um copo e a mãe — encaixada nas cenas do seu vídeo;
- ao gerar, o programa **desenha marcações coloridas** sobre o vídeo original para mostrar
  onde cada mudança aconteceria;
- todos os valores em R$ são **fictícios** e aparecem com "(simulado)". Nada é cobrado.

Por isso, para conhecer o programa, o melhor é usar o **vídeo de exemplo**: a história de
exemplo combina com ele.

## 2. Instalar no Windows

Você vai precisar de:

- **Docker Desktop** — o programa que "hospeda" o VideoDNA no seu computador. Baixe em
  https://www.docker.com/products/docker-desktop/, instale e abra. Na primeira vez ele pode
  pedir para instalar o WSL e reiniciar o computador; aceite. Ele está pronto quando mostra
  **"Engine running"**.
- **O código do VideoDNA.** Com o [Git](https://git-scm.com/download/win) instalado, abra o
  PowerShell e rode:

  ```powershell
  cd $HOME
  git clone --branch claude/amazing-keller-uj680z --depth 1 https://github.com/alexbarreto38-jpg/skills.git videodna
  ```

  Sem Git: baixe o arquivo ZIP em
  `https://github.com/alexbarreto38-jpg/skills/archive/refs/heads/claude/amazing-keller-uj680z.zip`
  e extraia numa pasta fácil de achar.

Depois, para **iniciar** (e sempre que quiser usar o programa):

```powershell
cd $HOME\videodna\videodna-studio
powershell -ExecutionPolicy Bypass -File .\iniciar.ps1
```

O `iniciar.ps1` confere o Docker, baixa e prepara tudo e abre o navegador em
http://localhost:3000. **Na primeira vez leva alguns minutos**; nas próximas, segundos. Se a
internet falhar no meio, rode o mesmo comando de novo: ele continua de onde parou.

| Para…                         | Rode, na pasta `videodna-studio`                                   |
|-------------------------------|---------------------------------------------------------------------|
| iniciar                       | `powershell -ExecutionPolicy Bypass -File .\iniciar.ps1`            |
| parar (seus projetos ficam)   | `powershell -ExecutionPolicy Bypass -File .\parar.ps1`              |
| atualizar para a versão nova  | `git pull` e depois o `iniciar.ps1`                                 |
| apagar tudo e começar do zero | `powershell -ExecutionPolicy Bypass -File .\parar.ps1 -ApagarDados` |

Depois de reiniciar o computador, basta abrir o Docker Desktop: o VideoDNA volta sozinho.

## 3. Primeira vez: o vídeo de exemplo

Na tela inicial, clique em **"Experimentar com um vídeo de exemplo"**. O programa cria um
projeto com um vídeo curto (12 segundos, 6 cenas) e já começa a análise — leva menos de um
minuto. Depois disso, siga as etapas abaixo com ele.

<!-- screenshots:home -->

## 4. As seis etapas

No topo de cada tela do projeto aparece a barra de etapas — **1 Enviar · 2 Analisar ·
3 Editar · 4 Revisar · 5 Gerar · 6 Comparar** —, com a etapa atual destacada e uma frase
dizendo o que fazer agora.

### 1. Enviar

Escolha o vídeo (MP4, MOV, WebM ou MKV) e marque a caixa confirmando que você tem direito de
usá-lo. Vídeos de celular, inclusive em pé, funcionam.

### 2. Analisar

O programa encontra as cenas, as pessoas, as roupas, os objetos e o cenário. Pode esperar
na tela; se fechar, a análise continua. Se algo interromper (o computador dormiu, o
programa foi fechado), aparece **"Analisar de novo"**.

<!-- screenshots:analysis -->

### 3. Editar

A tela tem três partes: a **lista de elementos** à esquerda, o **vídeo** no meio e as
**opções** à direita.

1. Clique num elemento — na lista ou direto na caixa sobre o vídeo.
2. Escolha uma opção. Ela aparece como **"Escolhido"**, mas **ainda não foi aplicada**: a
   barra no rodapé mostra o que essa mudança afeta.
3. Clique em **"Aplicar mudança"**. Ela entra em **"Suas mudanças"**, no painel da direita.

Dicas da etapa:

- **"Confirme o que é"**: quando a IA não tem certeza ("É um copo de vidro ou uma taça?"),
  responda antes de mudar o item — assim nada é trocado pela coisa errada.
- **"Ver no quadro"** mostra a mudança aplicada a um quadro do vídeo, antes de gerar.
- Errou? **Ctrl+Z** desfaz, **Ctrl+Shift+Z** refaz, e cada mudança tem um botão para removê-la.
- **Opções avançadas → "O que manter igual ao original"**: tudo vem ligado (a história, a
  câmera, os movimentos, o som e o tempo). Só desligue se quiser que aquilo também possa mudar.

<!-- screenshots:editor -->

### 4. Revisar

Antes de gastar qualquer coisa, a tela de revisão mostra **o que vai mudar** (antes →
depois), **quantas cenas** mudam, o **custo estimado** e o **tempo estimado**. Escolha:

- **Qualidade** — *Econômico* gasta menos; *Qualidade máxima* usa modelos melhores e tenta
  mais vezes; *Equilibrado* fica no meio.
- **Tipo de vídeo** — comece pelo **rascunho (720p)** para conferir; gere a **versão final
  (1080p)** quando estiver satisfeito.

Os detalhes técnicos por cena ficam guardados em "Ver detalhes por cena".

<!-- screenshots:review -->

### 5. Gerar

O programa gera **cena por cena** e confere cada uma. Se uma cena sai com problema (por
exemplo, o prato some no meio da queda), ele refaz **só aquele trecho**. Você pode sair da
página: a geração continua, e o editor mostra "Gerando seu vídeo… Ver progresso".

### 6. Comparar

Veja o **antes e o depois** lado a lado, deslizando a divisória ou alternando entre os dois.
Gostou? Gere a versão final e baixe o vídeo. Quer ajustar? Volte para Editar — suas
mudanças continuam lá.

<!-- screenshots:result -->

## 5. Como conseguir bons resultados

- **Mudanças simples dão mais certo.** Cor de roupa, cabelo e cenário de fundo costumam
  funcionar bem. Trocar um objeto que alguém segura, que cai e quebra é o caso mais difícil —
  o programa avisa com "mudança grande".
- **Faça primeiro o rascunho**, confira e só então gere a versão final.
- **Responda às dúvidas da IA** ("Confirme o que é") antes de mudar aqueles itens.
- **Poucas mudanças por vez** facilitam ver o que deu certo.

### Por que a IA pode errar — e o que o programa faz a respeito

Nenhuma IA de vídeo acerta tudo, e o VideoDNA foi feito partindo disso:

- **Para entender o vídeo**, duas IAs diferentes olham a mesma cena. Quando discordam, o
  programa não chuta: pergunta para você.
- **Para entender o seu pedido**, você não escreve um texto para a IA adivinhar — você clica
  no elemento e escolhe uma opção. As consequências (o prato tem que estar na mão, cair e
  quebrar) são calculadas por regras a partir da cena.
- **Para gerar**, cada cena é conferida depois de pronta e o trecho com problema é refeito.
  Se ainda assim não ficar bom, o programa marca "precisa de atenção" em vez de esconder.

## 6. O que significa

| Palavra | Quer dizer |
|---------|------------|
| Cena | Um trecho do vídeo entre dois cortes da câmera. |
| Elemento | Algo que dá para mudar: uma pessoa, uma roupa, um objeto, o cenário. |
| Video DNA | O mapa do seu vídeo: cenas, elementos, ações e o que acontece em cada momento. |
| Análise | A etapa em que o programa monta esse mapa. |
| Impacto | O quanto uma mudança mexe no vídeo: pequena, média ou grande. |
| Rascunho (720p) | Uma versão mais rápida e barata para conferir antes da final. |
| Versão final (1080p) | O vídeo na qualidade de entrega. |
| Certeza da IA | O quanto a IA tem certeza do que identificou. |
| Custo estimado | Quanto a geração deve custar com a IA real. Hoje, "(simulado)". |
| Modo demonstração | O modo atual, sem IA paga: análise e geração simuladas, valores fictícios. |

O mesmo glossário fica na página **Ajuda**, dentro do programa.

## 7. Problemas comuns

**"O Docker não está instalado" ou "O Docker Desktop não respondeu".** Abra o Docker Desktop
e espere "Engine running". Se ele falar de WSL ou virtualização, siga a instrução dele e
reinicie o computador.

**Erro de rede no primeiro início** (`timeout`, `TLS handshake`, `DeadlineExceeded`,
`i/o timeout`). É a conexão do Docker com a internet. Rode o `iniciar.ps1` de novo — ele
continua de onde parou. Se repetir: reinicie o Docker Desktop e desligue VPN durante a
instalação.

**A página http://localhost:3000 não abre** ("recusou a conexão"). O programa não está
rodando: rode o `iniciar.ps1`. Para ver o estado: `docker compose ps` na pasta
`videodna-studio` — `api` precisa aparecer como `healthy`.

**"Porta ocupada" (3000 ou 8000).** Outro programa está usando a porta. Feche-o e rode o
`iniciar.ps1` de novo.

**"O processamento foi interrompido".** O computador dormiu ou o programa foi fechado no meio
de uma análise ou geração. Clique para tentar de novo.

**"Não consegui me conectar ao VideoDNA".** O programa está desligado ou ainda iniciando.
Espere alguns segundos e clique em "Tentar de novo"; se continuar, rode o `iniciar.ps1`.

## 8. Seus vídeos e seus dados

- Tudo fica **no seu computador**, dentro do Docker. Nada é enviado para fora no modo
  demonstração.
- Ao enviar um vídeo, você confirma que tem direito de usá-lo; o programa guarda essa
  confirmação.
- Excluir um projeto apaga o projeto e toda a mídia dele. `parar.ps1 -ApagarDados` apaga
  tudo.
- Os vídeos gerados não levam os dados do arquivo original (como localização ou modelo do
  celular).
