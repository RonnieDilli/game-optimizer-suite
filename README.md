# Que Tela - Game Optimization Hub

Coletânea de scripts avançados, interface gráfica e especificações (SDD - Spec-Driven Development) para otimização agressiva de ambiente Windows, serviços de jogos e mitigação de *stuttering* em hardware de alto desempenho.

<img width="1052" height="782" alt="image" src="https://github.com/user-attachments/assets/248e0af3-e3e0-4caa-83e3-0bb3804b00cf" />
<img width="852" height="668" alt="image" src="https://github.com/user-attachments/assets/686542c4-eb57-41af-be00-16cb22fc0d18" />
<img width="1052" height="782" alt="image" src="https://github.com/user-attachments/assets/873d885f-7dcd-45b6-bca3-d9734b6ce37d" />


## Visão Geral

O objetivo desta suíte é garantir *frametimes* impecáveis em títulos competitivos (CS2 e Rocket League) ao gerenciar os gargalos de I/O causados por corrupção de WebCaches, Shader Caches do DirectX, bloqueios de arquivos (*File Locks*) impostos pelo kernel gráfico do Windows, e orquestrar de forma automatizada o versionamento de configurações de múltiplas contas.

## Arquitetura Modular

A suíte opera através de um Hub central, versionamento Git interno e scripts independentes, com auditoria em tempo real na pasta `logs/`:

* **`que_tela_hub.py` (A Interface Central):** Painel de controle em CustomTkinter. Gerencia sessões da Steam, dispara otimizações de Engine (CS2/RL) e serve como interface para o histórico de versionamento Git.
* **`scripts/hardware/`:** Contorna bloqueios do *Desktop Window Manager* (`dwm.exe`) limpando caches (DX/GL). O instalador `setup_autorun.bat` cria uma tarefa `SYSTEM` para limpeza automática no boot.
* **`scripts/steam/`:** Limpeza de caches, reparo de permissões e mitigação de erros VAC manipulando o BCD do Windows.
* **`scripts/games/`:**
    * **CS2 Sync & Optimizer:** Motor de base de conhecimento. Sincroniza `configs` (video, autoexec) e **Launch Options** em um Repositório Git Privado local (`backups/`). Detecta mudanças in-game automaticamente e permite rollback via Hub.
    * **Epic RL Repair:** Otimiza o *Epic Online Services* e gerencia as configurações da Unreal Engine 3.

## Versionamento Git Integrado
O sistema utiliza um repositório Git local para rastrear alterações. Toda vez que uma configuração de vídeo ou Launch Option é alterada pelo Hub, ou quando o sistema detecta uma alteração in-game (CS2/RL), um snapshot é criado automaticamente. Isso permite:
1. **Auditoria:** Ver exatamente o que mudou entre sessões de jogo.
2. **Rollback:** Restaurar qualquer configuração anterior com um clique.
## Instalação e Uso

1. **Setup de Inicialização:** Navegue até `scripts/hardware/`, clique com o botão direito em `setup_autorun.bat` e **Execute como Administrador**. Isso garante limpeza de GPU em nível de sistema.
2. **O Hub Gráfico:** Execute `python que_tela_hub.py`. O Hub detectará seu hardware (threads/Hz) para recomendar as melhores Launch Options no CS2 e otimizações de vídeo.
3. **Sincronização:** Use a aba "Central de Backups" para gerenciar o histórico de commits do seu Git local.
## Metodologia SDD
Todas as regras de negócio deste repositório são validadas pelas especificações BDD (Gherkin) na pasta `docs/specs/`, servindo como ponte de confiabilidade para futuras validações autônomas por LLMs locais usando ferramentas como `pytest-bdd`.

