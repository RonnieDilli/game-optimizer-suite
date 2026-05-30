Scenario: Auditoria e Integracao de Modulos
    Given que a limpeza do cache de texturas do Rocket League foi concluida
    When o modulo de hardware e invocado
    Then a chamada deve repassar o parametro "--auto"
    And as evidencias da exclusao de arquivos devem ser salvas em "logs/epic_rl_repair.log"