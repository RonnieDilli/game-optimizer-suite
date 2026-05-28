Feature: Epic Games e Rocket League Optimizer
  Para resolver problemas de micro-stuttering e limpar o EOS Overlay
  Eu quero limpar o webcache e delegar a limpeza grafica ao modulo de hardware

  Scenario: Limpeza do Epic Online Services
    Given que a Epic Games Launcher nao esta em execucao
    When eu rodo a limpeza padrao
    Then o cache do "EOSOverlay" deve ser deletado obrigatoriamente
    And os Demos do Rocket League so devem ser apagados mediante confirmacao explicita (Y/N)
