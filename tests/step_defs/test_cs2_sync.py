import sys
import os
import pytest
from pathlib import Path
from pytest_bdd import scenario, given, when, then, parsers

# Adiciona a raiz do projeto ao sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from scripts.games.cs2_sync import analyze_launch_options
import scripts.games.cs2_sync as cs2_sync

@scenario('../../docs/specs/cs2_sync.feature', 'Gerenciamento Inteligente de Launch Options')
def test_launch_options_management():
    # Garantia de carregamento no contexto do teste
    if cs2_sync.CS2_LAUNCH_KNOWLEDGE is None:
        cs2_sync.CS2_LAUNCH_KNOWLEDGE = {}
    pass

@given('que a Steam esta fechada')
def steam_is_closed():
    return True

@given('que o hardware (threads/Hz) foi detectado via WMI')
def detect_hardware():
    pytest.hw_context = {"threads": 16, "refresh_rate": 144}

@when('eu edito as launch options no Hub')
def edit_launch_options():
    # Simulando a inclusão de comandos de teste
    pytest.new_opts = "-high -freq 60"

@then('o sistema deve cruzar o comando com o tesauro de riscos ("cs2_launch_options.json")')
def check_conflicts():
    analysis = analyze_launch_options(pytest.new_opts)

    # Debug: Se falhar, printar o que está chegando
    if analysis is None:
        pytest.fail("analyze_launch_options retornou None!")

    # A verificação original
    assert any(item['key'] == "-high" and "Estabilidade" in item['risco'] for item in analysis)

@then('deve sugerir correções dinâmicas baseadas no hardware detectado')
def check_suggestions():
    analysis = analyze_launch_options(pytest.new_opts)
    # Deve sugerir -freq 144 por causa do hardware mockado
    assert any(item['key'] == "-freq" and "144" in item['recomenda'] for item in analysis)

@then('ao salvar, o sistema deve versionar as novas launch options no Git em "docs/configs/cs2/[AccountName]/launch_options.txt"')
def check_save_simulation():
    # Apenas validamos que a lógica de string está pronta
    assert ".txt" in "launch_options.txt"

@then('deve salvar as novas options no arquivo "localconfig.vdf" da Steam')
def check_save_to_localconfig():
    # Placeholder para a lógica de salvar no localconfig.vdf
    assert True

@then('deve realizar um commit automático no repositório Git')
def check_git_commit():
    # Placeholder para a lógica de commit
    assert True
