Feature: Agendamento de Limpeza no Boot
  Para contornar o bloqueio de arquivos (File Lock) feito pelo DWM.exe e Windows Explorer
  Eu quero agendar a limpeza de GPU para ocorrer automaticamente na inicializacao do sistema

  Scenario: Criacao de Tarefa Oculta no Task Scheduler via VBScript
    Given que o script de setup e executado como Administrador
    When a rotina de agendamento e chamada
    Then uma tarefa chamada "GameOpt_GPU_BootCleanup" deve ser criada no Windows
    And o gatilho deve ser na Inicializacao do Sistema (ONSTART)
    And a execucao deve ocorrer com o usuario "SYSTEM" para evitar telas pretas
    And a chamada deve ser encapsulada em um VBScript para garantir 100% de invisibilidade