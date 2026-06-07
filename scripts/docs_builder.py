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

if __name__ == "__main__":
    print("Iniciando reconstrução dos guias técnicos...")
    build_cs2_video_guide()
    print("Processo concluido!")