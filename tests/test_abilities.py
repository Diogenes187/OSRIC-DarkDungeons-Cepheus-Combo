"""Spot-checks of the OSRIC ability tables against the Player Guide (Ch. 1)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.data import abilities as ab


def test_strength():
    assert ab.strength_mods(3) == dict(to_hit=-3, damage=-1, encumbrance=0,
                                       minor_test=1, major_test=0)
    assert ab.strength_mods(5)["to_hit"] == -2          # 4-5 share a row
    assert ab.strength_mods(16)["damage"] == 1
    assert ab.strength_mods(18)["damage"] == 2          # plain 18
    # exceptional Strength bands
    assert ab.strength_mods(18, 1)["damage"] == 3       # 18.01-18.50
    assert ab.strength_mods(18, 75)["to_hit"] == 2      # 18.51-18.75
    assert ab.strength_mods(18, 95)["damage"] == 5      # 18.91-18.99
    assert ab.strength_mods(18, 100) == ab.strength_mods(19)  # 18(00) == 19
    assert ab.strength_mods(19)["to_hit"] == 3 and ab.strength_mods(19)["damage"] == 6


def test_dexterity():
    assert ab.dexterity_mods(3)["ac_adj"] == 4          # descending: +4 (worse)
    assert ab.dexterity_mods(10)["ac_adj"] == 0
    assert ab.dexterity_mods(15)["ac_adj"] == -1        # better AC
    assert ab.dexterity_mods(18)["missile_to_hit"] == 3
    assert ab.dexterity_mods(18)["initiative"] == -3


def test_constitution():
    assert ab.constitution_mods(3)["hp_mod"] == -2
    assert ab.constitution_mods(15)["hp_mod"] == 1
    assert ab.constitution_mods(17)["hp_mod"] == 2              # non-warrior
    assert ab.constitution_mods(17, warrior=True)["hp_mod"] == 3
    assert ab.constitution_mods(18, warrior=True)["hp_mod"] == 4
    assert ab.constitution_mods(9)["system_shock"] == 65


def test_mental_abilities():
    assert ab.intelligence_languages(7) == 0
    assert ab.intelligence_languages(8) == 1
    assert ab.intelligence_languages(18) == 7
    assert ab.wisdom_mental_save(7) == -1
    assert ab.wisdom_mental_save(15) == 1
    assert ab.wisdom_mental_save(19) == 5


def test_charisma():
    assert ab.charisma_mods(8)["loyalty"] == -5
    assert ab.charisma_mods(10)["sidekicks"] == 4       # 9-11 share a row
    assert ab.charisma_mods(18)["reaction"] == 35
    assert ab.charisma_mods(15)["loyalty"] == 15


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All ability-table tests passed.")
