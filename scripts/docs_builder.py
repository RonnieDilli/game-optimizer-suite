import os
import sys
from pathlib import Path

# Adiciona o diretório de jogos ao PATH para importar a Antologia
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "scripts" / "games"))
import cs2_sync

def build_cs2_video_guide():
    """Gera o Guia de Otimizacao do CS2 baseado na Knowledge Base viva do codigo."""
    guide_path = BASE_DIR / "docs" / "CS2_VIDEO_CONFIG_GUIDE.md"
    
    content = [
        "# 🎮 Guia Vivo de Otimização (CS2)",
        "Este documento é gerado automaticamente a partir da Base de Conhecimento do *Que Tela Hub*.",
        "---",
        "## 🚀 Dicionário de Variáveis (Antologia da Source 2)\n"
    ]
    
    for key, data in cs2_sync.CS2_KNOWLEDGE_BASE.items():
        content.append(f"### `{key}` ({data['nome']})")
        content.append(f"* **Valor Recomendado:** `{data['ideal']}`")
        content.append(f"* **Impacto na Engine:** {data['impacto']}\n")
        
    guide_path.parent.mkdir(parents=True, exist_ok=True)
    guide_path.write_text("\n".join(content), encoding="utf-8")
    print(f"[OK] {guide_path.name} gerado.")

def build_readme():
    readme_path = BASE_DIR / "README.md"
    content = """# Que Tela - Game Optimization Hub

O **Que Tela** é um ecossistema completo de otimização de *frametime* e gestão de configurações, construído em Python e Batch, operando sob uma arquitetura de privilégios segmentados (Zero-Trust UAC).

## Arquitetura de Software

*   **Hub Interativo (`que_tela_hub.py`):** Interface gráfica (GUI) construída em CustomTkinter. Executa no espaço do usuário, monitora o estado de processos (Steam, CS2, Epic) em tempo real e atua como um *Log Watcher* para tarefas assíncronas em Batch.
*   **Gestão de Estado (Sessões):** Manipulação da chave de registro `AutoLoginUser` da Steam, permitindo trocas de smurf instantâneas sem exigir elevação de administrador.
*   **Motor de Análise (Diff View):** Utiliza uma base de conhecimento embutida (Antologia) para auditar as configurações da Source 2 (`cs2_video.txt`) comparando-as com parâmetros ideais de alocação de threads e Reflex.
*   **Versionamento Nativo (Git):** O hub isola as configurações do jogo em um repositório privado (`CS2_Private_Configs`), com suporte nativo para `git init`, `commit` automatizado, navegação de histórico (`git log`) e sistema de *Rollback* instantâneo.
*   **Delegação de Privilégios (.bat):** Tarefas sensíveis (limpeza de GPU em `LocalLow`, manipulação do `SteamService`) são isoladas em scripts Batch e invocadas através de `ShellExecuteW`, disparando o UAC estritamente no momento da ação.

## 📖 Documentação Gerada
* [Guia de Configurações da Source 2 (Auto-Gerado)](docs/CS2_VIDEO_CONFIG_GUIDE.md)
"""
    readme_path.write_text(content, encoding="utf-8")
    print(f"[OK] README.md gerado.")

if __name__ == "__main__":
    print("Iniciando reconstrução da documentação...")
    build_cs2_video_guide()
    build_readme()
    print("Processo concluido!")