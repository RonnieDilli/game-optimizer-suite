Feature: Sincronizacao de Contas e Configuracoes do CS2
  Para manter frametimes estaveis e alternar agilmente entre contas/smurfs
  Eu quero gerenciar as sessoes da Steam via Registro do Windows e otimizar as configs de video de forma dinamica e segura

  Scenario: Troca de Sessao da Steam Silenciosa
    Given que a aplicacao Steam.exe e encerrada a forca
    When eu seleciono uma conta no menu interativo oriunda do parse do arquivo "loginusers.vdf"
    Then a chave de registro "AutoLoginUser" deve ser preenchida com o "AccountName" selecionado
    And a chave "RememberPassword" deve ser definida como 1 (REG_DWORD) para pular o prompt
    And a Steam deve ser reiniciada assumindo o novo perfil automaticamente

  Scenario: Protecao de Hardware e Preservacao de Resolucao
    Given que eu solicitei a otimizacao do arquivo "cs2_video.txt"
    And a rotina WMI detectou o VendorID e DeviceID reais da placa de video primaria
    When o script for injetar o template otimizado "cs2_video_base.txt"
    Then o script deve primeiro ler e salvar a resolucao e frequencia atual (Hz) do usuario
    And deve comparar os IDs fisicos da GPU com os IDs gravados no arquivo
    And deve alertar sobre uma possivel divergencia de hardware antes de prosseguir
    And deve fixar o parametro "AutoConfig" em "0" para prevenir o reset forcado da Source 2

  Scenario: Sincronizacao de Arquivos Locais para Versionamento Git
    Given que a otimizacao de desempenho foi concluida
    When a rotina de sincronizacao for acionada pelo script Python
    Then os arquivos sensiveis de configuracao ("cs2_video.txt", "autoexec.cfg", "config.cfg")
    And devem ser copiados da pasta userdata do usuario na Steam
    And colados com sucesso no caminho "docs/configs/cs2/[AccountName]/" do repositorio local
    And o arquivo "launch_options.txt" contendo as opcoes de inicializacao atuais deve ser versionado no mesmo diretorio

  Scenario: Gerenciamento Inteligente de Launch Options
    Given que a Steam esta fechada
    And que o hardware detectou o contexto atual do PC
    When eu edito as launch options para incluir novos comandos
    Then o sistema deve verificar se existem conflitos conhecidos no tesauro
    And deve sugerir correções dinâmicas baseadas no hardware detectado
    And ao salvar, o sistema deve versionar as novas launch options no Git em "docs/configs/cs2/[AccountName]/launch_options.txt"
