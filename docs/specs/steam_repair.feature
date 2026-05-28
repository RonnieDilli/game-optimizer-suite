Feature: Steam Repair Modular
  Para limpar caches acumulados e reparar a Steam
  Eu quero executar uma rotina que delegue a limpeza de GPU para o modulo de hardware

  Scenario: Chamada de Modulo Externo
    Given que a limpeza especifica da Steam foi concluida
    When o script atinge a fase de limpeza de hardware
    Then ele deve invocar "scripts\hardware\gpu_os_cleanup.bat"
    And aguardar o retorno da execucao antes de exibir o resumo final
