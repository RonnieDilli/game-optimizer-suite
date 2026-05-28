Feature: Limpeza de Shaders e SO (Modulo Base)
  Para garantir frametimes consistentes e evitar stuttering
  Como um modulo central de manutencao
  Eu quero parar os servicos de video temporariamente para liberar o lock de arquivos de cache

  Scenario: Limpeza profunda de Shaders (NVIDIA/AMD)
    Given que o script e executado com privilegios de Administrador
    When a rotina de limpeza de hardware e chamada
    Then o servico "NVDisplay.ContainerLocalSystem" deve ser interrompido
    And os diretorios "DXCache" e "GLCache" da NVIDIA devem ser deletados
    And o diretorio "DxCache" da AMD deve ser deletado
    And o servico "NVDisplay.ContainerLocalSystem" deve ser reiniciado
