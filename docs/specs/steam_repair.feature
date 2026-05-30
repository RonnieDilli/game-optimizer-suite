Scenario: Modo Silencioso e Prevencao de Perda de Dados
    Given que o script da Steam e executado com o argumento "--auto"
    When chegar a fase de perguntas iniciais (Login e VAC)
    Then os prompts devem ser ignorados assumindo "N" por padrao
    And todas as acoes e contagens de arquivos devem ser registradas em "logs/steam_repair.log"