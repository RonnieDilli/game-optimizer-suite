Feature: Limpeza de Shaders e SO (Modulo Base)
  Para garantir frametimes consistentes e evitar stuttering
  Como um modulo central de manutencao
  Eu quero parar os servicos de video temporariamente e limpar os caches em todos os perfis

  Scenario: Limpeza profunda de Shaders com Varredura Absoluta
    Given que o script e executado com privilegios de Administrador
    When a rotina de limpeza de hardware e chamada
    Then o servico "NVDisplay.ContainerLocalSystem" deve ser interrompido se estiver em execucao
    And os diretorios "DXCache" e "GLCache" de todos os usuarios na pasta "Local" devem ser deletados
    And os caches em pastas restritas como "LocalLow" tambem devem ser limpos
    And o servico NVIDIA deve ser restaurado ao seu estado original

  Scenario: Execucao Autonoma e Geracao de Logs
    Given que o script foi chamado com o parametro "--auto"
    When o processamento for concluido
    Then um relatorio de auditoria deve ser gerado em "logs/gpu_cleanup.log"
    And a janela do terminal deve ser encerrada sem exigir interacao do usuario (sem pause)