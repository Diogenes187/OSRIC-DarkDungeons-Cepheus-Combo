"""Checks the bestiary loaded from the extracted stat blocks."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from engine.data import monsters as mon


def test_bestiary_loaded():
    assert len(mon.BESTIARY) > 200, "run scripts/extract_monsters.py"


def test_known_monsters():
    g = mon.get("Goblin")
    assert g is not None
    assert g.ac_descending == 6 and g.ac_ascending == 14
    o = mon.get("Hobgoblin")
    assert o and o.ac_descending == 5
    # Giants are tougher and hit harder.
    fg = mon.get("Giant, Fire") or mon.get("Fire Giant")
    if fg:
        assert fg.hd_value >= 10 and fg.attack_bonus >= 9


def test_combat_fields():
    g = mon.get("Goblin")
    # Goblin attack bonus = fighter at ~1 HD = 0.
    assert g.attack_bonus == 0
    # Primary damage parses to a dice expression.
    assert "d" in g.primary_damage()
    # HP is rolled within a sane range for a 1-1 HD goblin.
    d = Dice(seed=1)
    hps = [g.roll_hp(d) for _ in range(200)]
    assert all(1 <= h <= 8 for h in hps)


def test_to_combatant_fights():
    from engine import combat
    d = Dice(seed=7)
    ogre = mon.get("Ogre")
    assert ogre is not None
    foe = mon.to_combatant(d, ogre)
    hero = combat.Combatant(name="Faelith", hp=10, hp_max=10, ac_descending=4,
                            attack_bonus=0, damage_dice="1d8")
    # A swing resolves and can deal damage.
    r = combat.resolve_attack(hero, foe, d)
    assert "hit" in r and foe.ac_ascending == 20 - ogre.ac_descending


def test_search():
    res = mon.search("giant")
    assert any("giant" in m.name.lower() for m in res)


def test_curated_supplement_recovered():
    # Common monsters lost to the column-format blocks, restored via supplement.
    for name in ("Ogre", "Wolf", "Bear, Brown", "Lizard Man", "Zombie",
                 "Tiger", "Snake, Cobra", "Carrion Crawler",
                 "Dragon, Red", "Elemental, Fire", "Naga, Guardian", "Djinni",
                 "Rhinoceros", "Beetle, Water", "Eagle, Giant", "Mephit, Lava"):
        m = mon.get(name)
        assert m is not None, "missing curated monster: {}".format(name)
        assert m.ac_descending is not None and m.attack_bonus >= 0
    # Wolf should be a real, fightable stat block.
    w = mon.get("Wolf")
    assert w.hd_value == 2 and "d" in w.primary_damage()


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All bestiary tests passed.")
