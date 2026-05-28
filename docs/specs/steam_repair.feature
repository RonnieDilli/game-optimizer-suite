Feature: Steam Repair and Cache Cleanup
  Para garantir a estabilidade e performance dos jogos
  Como um usuario de PC focado em otimizacao
  Eu quero limpar caches acumulados e reparar o servico da Steam de forma segura

  Scenario: Verificacao de Privilegios Administrativos
    Given que o script e executado
    When os privilegios de administrador nao sao detectados via net session
    Then o script deve exibir um erro critico
    And a execucao deve ser abortada imediatamente

  Scenario: Exclusao Forcada de Dados de Login com Aviso
    Given que um aviso explicito sobre a perda do Steam Guard foi exibido
    And eu confirmei a remocao de dados
    When eu executo a rotina
    Then o arquivo "loginusers.vdf" deve ser deletado
    And os tokens "ssfn" devem ser apagados

  Scenario: Correcao de VAC e Reinicializacao
    Given que as correcoes de VAC foram solicitadas
    When a execucao termina
    Then o parametro DEP deve ser configurado seguramente como OptIn
    And o sistema deve sugerir uma reinicializacao para efetivar as alteracoes do bcdedit
