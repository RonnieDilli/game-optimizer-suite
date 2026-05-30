# Game Optimization Suite

Coletânea de scripts avançados e especificações (SDD - Spec-Driven Development) para otimização agressiva de ambiente Windows, serviços de jogos e mitigação de *stuttering* em hardware de alto desempenho.

## Visão Geral

O objetivo desta suíte é garantir *frametimes* impecáveis em títulos competitivos (CS2 e Rocket League) ao gerenciar os gargalos de I/O causados por corrupção de WebCaches, Shader Caches do DirectX e bloqueios de arquivos (*File Locks*) impostos pelo kernel gráfico do Windows.

## Arquitetura Modular

A suíte opera de forma independente ou orquestrada, gerando auditoria em tempo real na pasta `logs/`:

* **`scripts/hardware/` (Módulo Base):** * Contorna os bloqueios do *Desktop Window Manager* (`dwm.exe`) parando temporariamente a telemetria da placa de vídeo.
    * Faz varredura em todos os perfis (`Local` e `LocalLow`) limpando o `DXCache` e `GLCache`.
    * **Auto-Run Setup:** Inclui um instalador VBScript (`setup_autorun.bat`) que registra a limpeza de GPU para rodar invisível sob a conta `SYSTEM` a cada inicialização do Windows (OnStart).
* **`scripts/steam/`:** * Limpeza dinâmica de caches do CS2, HTML da loja, reparo de permissões do `SteamService` e renovação segura de tokens do *Steam Guard*.
    * Aplica mitigação para o erro *"VAC was unable to verify your game session"* manipulando o BCD do Windows de forma segura (`nx OptIn`).
* **`scripts/games/`:** * Foco em otimização do *Epic Online Services* (EOS Overlay) que sabota o *frametime*.
    * Esvazia o cache de renderização de texturas e menus do Rocket League (`TAGame/Cache`).

## Instalação e Uso

1.  **Limpeza Contínua (Recomendado):** Navegue até `scripts/hardware/`, clique com o botão direito em `setup_autorun.bat` e **Execute como Administrador**. Isso garante que sua GPU inicie 100% limpa todos os dias.
2.  **Manutenção Manual:** Sempre que o jogo engasgar ou após uma atualização de drivers, execute `steam_repair.bat` ou `epic_rl_repair.bat` como Administrador. Eles interrogarão você sobre exclusões severas (como limpar contas ou *replays*) antes de prosseguir.
3.  **Modo Silencioso:** Qualquer script chamado com o argumento `--auto` rodará em *background*, assumirá respostas seguras ("Não") para exclusão de dados sensíveis e fará log do resultado sem pausar a tela.

## Metodologia SDD
Todas as regras de negócio deste repositório são validadas pelas especificações na pasta `docs/specs/`, permitindo futuras integrações com motores de teste baseados em Gherkin (ex: `pytest-bdd`) usando LLMs locais para auditoria do código.