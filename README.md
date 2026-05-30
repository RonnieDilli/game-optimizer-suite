# Game Optimization Suite

Coletânea de scripts avançados e especificações (SDD - Spec-Driven Development) para otimização agressiva de ambiente Windows, serviços de jogos e mitigação de *stuttering* em hardware de alto desempenho.

## Visão Geral

O objetivo desta suíte é garantir *frametimes* impecáveis em títulos competitivos (CS2 e Rocket League) ao gerenciar os gargalos de I/O causados por corrupção de WebCaches, Shader Caches do DirectX, bloqueios de arquivos (*File Locks*) impostos pelo kernel gráfico do Windows, e orquestrar de forma automatizada o versionamento de configurações de múltiplas contas.

## Arquitetura Modular

A suíte opera de forma independente ou orquestrada, gerando auditoria em tempo real na pasta `logs/`:

* **`scripts/hardware/` (Módulo Base):** * Contorna os bloqueios do *Desktop Window Manager* (`dwm.exe`) parando temporariamente a telemetria da placa de vídeo.
    * Faz varredura em todos os perfis (`Local` e `LocalLow`) limpando o `DXCache` e `GLCache`.
    * **Auto-Run Setup:** Inclui um instalador VBScript (`setup_autorun.bat`) que registra a limpeza de GPU para rodar invisível sob a conta `SYSTEM` a cada inicialização do Windows (OnStart).
* **`scripts/steam/`:** * Limpeza dinâmica de caches do CS2, HTML da loja, reparo de permissões do `SteamService` e renovação segura de tokens do *Steam Guard*.
    * Aplica mitigação para o erro *"VAC was unable to verify your game session"* manipulando o BCD do Windows de forma segura (`nx OptIn`).
* **`scripts/games/`:** * **Epic Games e Rocket League (`epic_rl_repair.bat`):** Foco em otimização do *Epic Online Services* (EOS Overlay) que sabota o *frametime* e limpeza gráfica (`TAGame/Cache`).
    * **CS2 Sync & Optimizer (`cs2_sync.py`):** Script Python interativo para troca dinâmica de contas de forma rápida (manipulando `AutoLoginUser`), injeção segura de *templates* de vídeo (`AutoConfig 0` com hardware WMI real) e sincronização contínua das `configs` no repositório.

## Instalação e Uso

1.  **Limpeza Contínua (Recomendado):** Navegue até `scripts/hardware/`, clique com o botão direito em `setup_autorun.bat` e **Execute como Administrador**. Isso garante que sua placa de vídeo inicie 100% livre de bloqueios todos os dias.
2.  **Manutenção de Stuttering:** Sempre que o jogo engasgar ou após atualização de drivers de vídeo, execute `steam_repair.bat` ou `epic_rl_repair.bat` como Administrador.
3.  **Modo Silencioso:** Qualquer script Batch chamado com o argumento `--auto` rodará em *background*, assumirá respostas seguras ("Não") para exclusão de dados sensíveis e auditará as exclusões em `logs/`.
4.  **Gestão de Contas CS2:** Execute `python scripts/games/cs2_sync.py` no terminal para alternar entre *smurfs*/principais, injetar perfis de máximo desempenho e empurrar seu `autoexec.cfg` para a estrutura do Git.

## Metodologia SDD
Todas as regras de negócio deste repositório são validadas pelas especificações BDD (Gherkin) na pasta `docs/specs/`, servindo como ponte de confiabilidade para futuras validações autônomas por LLMs locais usando ferramentas como `pytest-bdd`.