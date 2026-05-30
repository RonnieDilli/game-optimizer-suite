# Que Tela - Game Optimization Hub

Coletânea de scripts avançados, interface gráfica e especificações (SDD - Spec-Driven Development) para otimização agressiva de ambiente Windows, serviços de jogos e mitigação de *stuttering* em hardware de alto desempenho.

## Visão Geral

O objetivo desta suíte é garantir *frametimes* impecáveis em títulos competitivos (CS2 e Rocket League) ao gerenciar os gargalos de I/O causados por corrupção de WebCaches, Shader Caches do DirectX, bloqueios de arquivos (*File Locks*) impostos pelo kernel gráfico do Windows, e orquestrar de forma automatizada o versionamento de configurações de múltiplas contas.

## Arquitetura Modular

A suíte opera através de um Hub central ou scripts independentes, gerando auditoria em tempo real na pasta `logs/`:

* **`que_tela_hub.py` (A Interface Central):** Painel de controle construído em CustomTkinter. Opera sem exigir privilégios globais de Administrador, monitora os jogos ao vivo, permite troca de contas da Steam em um clique e aciona ferramentas de limpeza via UAC sob demanda.
* **`scripts/hardware/` (Módulo Base):** * Contorna os bloqueios do *Desktop Window Manager* (`dwm.exe`) parando temporariamente a telemetria da placa de vídeo.
    * Faz varredura em todos os perfis (`Local` e `LocalLow`) limpando o `DXCache` e `GLCache`.
    * **Auto-Run Setup:** Inclui um instalador VBScript (`setup_autorun.bat`) que registra a limpeza de GPU para rodar invisível sob a conta `SYSTEM` a cada inicialização do Windows (OnStart).
* **`scripts/steam/`:** * Limpeza dinâmica de caches do CS2, HTML da loja, reparo de permissões do `SteamService`.
    * Aplica mitigação para o erro *"VAC was unable to verify your game session"* manipulando o BCD do Windows de forma segura (`nx OptIn`).
* **`scripts/games/`:** * **Epic Games e Rocket League (`epic_rl_repair.bat`):** Foco em otimização do *Epic Online Services* (EOS Overlay) que sabota o *frametime* e limpeza gráfica (`TAGame/Cache`).
    * **CS2 Sync & Optimizer (`cs2_sync.py`):** Motor de base de conhecimento. Injeta de forma seletiva *templates* de vídeo (`AutoConfig 0` com hardware WMI real) e sincroniza suas `configs` em um **Repositório Git Privado**, separado do código da aplicação.
    * 📖 **[LEIA AQUI: Guia Completo de Otimização de Vídeo do CS2](docs/CS2_VIDEO_CONFIG_GUIDE.md)**

## Instalação e Uso

1.  **O Hub Gráfico:** Execute `python que_tela_hub.py` no terminal. O aplicativo abrirá em modo usuário para gestão de contas da Steam e auditoria do CS2. Ele pedirá permissão de Administrador automaticamente apenas quando você executar rotinas de limpeza profunda.
2.  **Limpeza Contínua no Boot:** Navegue até `scripts/hardware/`, clique com o botão direito em `setup_autorun.bat` e **Execute como Administrador**. Isso garante que sua placa de vídeo inicie 100% livre de bloqueios de cache todos os dias antes da interface do Windows carregar.
3.  **Execução Silenciosa por CLI:** Qualquer script Batch chamado com o argumento `--auto` rodará em *background*, assumirá respostas seguras ("Não") para exclusão de dados sensíveis e auditará as exclusões na pasta `logs/`.

## Metodologia SDD
Todas as regras de negócio deste repositório são validadas pelas especificações BDD (Gherkin) na pasta `docs/specs/`, servindo como ponte de confiabilidade para futuras validações autônomas por LLMs locais usando ferramentas como `pytest-bdd`.