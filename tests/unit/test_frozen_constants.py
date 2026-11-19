"""Module-level lookup tables are frozendicts, so nothing can change them at runtime."""

import pytest
from src.bot.constants import variables
from src.gw2.constants import gw2_currencies, gw2_teams

FROZEN_CONSTANTS = {
    "AI_MODEL_PROVIDERS": variables.AI_MODEL_PROVIDERS,
    "WALLET_MAPPING": gw2_currencies.WALLET_MAPPING,
    "WALLET_DISPLAY_NAMES": gw2_currencies.WALLET_DISPLAY_NAMES,
    "ACHIEVEMENT_MAPPING": gw2_currencies.ACHIEVEMENT_MAPPING,
    "WR_TEAM_NAMES": gw2_teams.WR_TEAM_NAMES,
}


@pytest.mark.parametrize("name", FROZEN_CONSTANTS)
def test_constant_is_frozendict(name):
    assert isinstance(FROZEN_CONSTANTS[name], frozendict)


@pytest.mark.parametrize("name", FROZEN_CONSTANTS)
def test_constant_cannot_be_modified(name):
    table = FROZEN_CONSTANTS[name]
    some_key = next(iter(table))
    with pytest.raises(TypeError):
        table[some_key] = "changed"
    with pytest.raises(AttributeError):
        table.update({})
