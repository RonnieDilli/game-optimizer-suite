Feature: Agendamento de Limpeza no Boot
  Para contornar o bloqueio de arquivos (File Lock) feito pelo DWM.exe e Windows Explorer
  Eu quero agendar a limpeza de GPU para ocorrer automaticamente no logon do sistema

  Scenario: Criacao de Tarefa Oculta no Task Scheduler
    Given que o script de setup e executado como Administrador
    When a rotina de agendamento e chamada
    Then uma tarefa chamada "GameOpt_GPU_BootCleanup" deve ser criada no Windows
    And o gatilho deve ser "Ao fazer logon" (ONLOGON)
    And a execucao deve ocorrer com privilegios maximos (Highest)
    And a chamada deve ser encapsulada em um PowerShell Hidden para nao exibir janelas
