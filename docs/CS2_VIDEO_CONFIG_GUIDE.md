# 🎮 Guia de Configuração e Otimização de Vídeo (CS2)

O arquivo `cs2_video.txt` lida com a camada mais baixa de renderização do motor Source 2. Modificá-lo de forma inteligente é essencial para setups de alta performance (como a linha RTX 3080/3090 combinada com Ryzen 9). 

Nossa suíte utiliza *templates* para aplicar otimizações agressivas enquanto preserva a sua preferência de monitor. Abaixo está a dissecação técnica das variáveis que o nosso script gerencia.

---

## 🔒 Preservação de Hardware (Intocáveis pelo Template)
O script extrai e mantém estas configurações do seu arquivo original antes de aplicar a otimização. Mexer nisso acidentalmente quebra o jogo.

* **`VendorID` e `DeviceID`:** Identificam fisicamente a GPU (ex: `4318` e `8710` representam uma RTX 3080). 
  * *Por que preservar:* Se o CS2 detectar uma string incompatível com o hardware atual, ele entra em modo de segurança, deleta o arquivo e reseta tudo para as piores configurações possíveis.
* **A Tríade do Monitor (`defaultres`, `defaultresheight`, `refreshrate_*`):** Define a contagem de pixels e os ciclos do monitor.
  * *Por que preservar:* Forçar os numeradores de atualização de 240Hz (ex: `239761 / 1000`) em uma tela de 144Hz ou 60Hz causa "Black Screen" (Sinal Ausente) imediata ao abrir o jogo.
* **`monitor_index` e `fullscreen`:** * *Por que preservar:* Garante que o jogo abra sempre no monitor principal do usuário (`0`) e obrigatoriamente no modo tela cheia nativo (`1`). O modo "Janela sem Bordas" injeta o *buffer* do DWM (*Desktop Window Manager*) do Windows, o que adiciona um atraso fatal (*input lag*) em jogos competitivos.

---

## 🚀 Otimização de Performance (Injetadas pelo Template)
Sempre que o script `cs2_sync.py` roda, ele força estas variáveis para garantir máxima prioridade ao CS2 no sistema operacional.

* **`AutoConfig "0"`:** Travar essa variável em zero desabilita o *benchmark* oculto da Source 2 durante o boot. O jogo é obrigado a engolir as configurações escritas no arquivo de texto, blindando suas alterações personalizadas contra resets.
* **`setting.r_low_latency "2"`:** Ativa o NVIDIA Reflex no modo **On + Boost**. Isso força a GPU a manter os *clocks* de renderização no máximo absoluto, mesmo em cenas leves, reduzindo a fila de quadros (*Render Queue*) entre a CPU e o processador gráfico. O resultado são latências de sistema submilisegundo.
* **`setting.cpu_level`, `setting.gpu_level` e `setting.gpu_mem_level`:** * Setando todas para `"3"` (Max), nós instruímos a *engine* a utilizar todo o *pool* de memória gráfica (VRAM) disponível na placa e a paralelizar agressivamente as threads virtuais da CPU (Ryzen). Isso evita a redução artificial de uso de recursos, prevenindo que o jogo "durma" no meio da partida, causando *micro-stutterings*.

---

### Sincronização via Git
Como esse arquivo é salvo no repositório local em `docs/configs/cs2/[NomeDaConta]/`, qualquer alteração gráfica que você fizer pelos menus do CS2 poderá ser auditada rodando um `git diff` antes do commit, permitindo que você descubra exatamente qual variável da *Source 2* foi afetada pela alteração visual.