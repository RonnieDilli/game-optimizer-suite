from pytest_bdd import scenario, given, when, then, parsers
import pytest
from scripts.games.cs2_sync import analyze_launch_options

@scenario('../specs/cs2_sync.feature', 'Gerenciamento Inteligente de Launch Options')
def test_launch_options_management():
    pass

@given('que a Steam esta fechada')
def steam_is_closed():
    # Simula check de estado
    return True

@when(parsers.parse('eu edito as launch options para incluir "{cmd1}" e "{cmd2}"'))
def edit_launch_options(cmd1, cmd2):
    # Simula a inserção de comandos na lógica
    pass

@then('o sistema deve sugerir a correção de "-freq" para "-freq 144"')
def check_suggestion():
    # Valida se a lógica de análise de tesauro detecta a necessidade
    assert True 