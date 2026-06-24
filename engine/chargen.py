"""chargen.py -- OSRIC 3.0 character creation as a seeded, replayable coroutine.

Same proven shape as the Cepheus lifepath: a generator that yields a decision,
receives a choice, and advances -- so a build is fully reconstructed by replaying
its seed + ordered choices (restart-proof, deterministic). The dice come from a
seeded engine.dice.Dice; choices that consume randomness (rerolls) replay
identically.

Flow:
  ability_method -> (roll & assign  | input)  -> choose_ancestry -> choose_class
  -> choose_alignment -> [auto: hp, exceptional STR, AC, gold] -> name_character
  -> complete

The campaign's `allow_overrides` flag waives racial class restrictions, class
ability minimums, and (later) level limits -- old-school Greyhawk "anything goes".
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .dice import Dice
from .data import abilities as ab
from .data import races as races_mod
from .data import classes as classes_mod

ORDER = ("str", "dex", "con", "int", "wis", "cha")
ABILITY_LABELS = {"str": "Strength", "dex": "Dexterity", "con": "Constitution",
                  "int": "Intelligence", "wis": "Wisdom", "cha": "Charisma"}
WARRIORS = ("Fighter", "Paladin", "Ranger")
ALL_ALIGNMENTS = ("LG", "LN", "LE", "NG", "N", "NE", "CG", "CN", "CE")
_METHOD_ROLLERS = {
    "3d6": lambda d: d.ability_3d6().natural,
    "4d6": lambda d: d.ability_4d6_drop_lowest().natural,
    "5d6": lambda d: d.ability_5d6_drop_two().natural,
}


@dataclass
class Character:
    name: str = "Unnamed"
    race: Optional[str] = None
    char_class: Optional[str] = None
    classes_list: List[str] = field(default_factory=list)
    alignment: Optional[str] = None
    scores: Dict[str, int] = field(default_factory=dict)
    str_pct: int = 0
    hp_max: int = 0
    ac_descending: int = 10
    ac_ascending: int = 10
    gold: int = 0
    gear: List[str] = field(default_factory=list)
    xp_bonus: bool = False
    log: List[str] = field(default_factory=list)

    def to_repo_dict(self) -> Dict[str, Any]:
        """Shape expected by state.repo.Repo.save_character."""
        all_classes = self.classes_list or ([self.char_class] if self.char_class else [])
        d = {
            "name": self.name, "race": self.race,
            "classes": [{"class": cl, "level": 1, "xp": 0} for cl in all_classes],
            "alignment": self.alignment, "str_pct": self.str_pct,
            "hp_max": self.hp_max, "ac_descending": self.ac_descending,
            "ac_ascending": self.ac_ascending, "gold": self.gold,
            "gear": list(self.gear),
            "notes": ("Prime-requisite XP bonus (+10%)." if self.xp_bonus else ""),
        }
        d.update({a: self.scores.get(a) for a in ORDER})
        return d


class CharacterCreator:
    def __init__(self, name: str = "Recruit", seed: Optional[int] = None,
                 allow_overrides: bool = False):
        self.seed = seed if seed is not None else random.Random().randint(0, 2**31 - 1)
        self.dice = Dice(self.seed)
        self.allow_overrides = allow_overrides
        self.char = Character(name=name)
        self.feed: List[str] = []
        self.complete = False
        self._gen = self._script()
        self.current = next(self._gen)

    # ---- public API ----------------------------------------------------
    def pending(self) -> Optional[Dict[str, Any]]:
        return self.current

    def choose(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self.complete:
            return self.current
        try:
            self.current = self._gen.send(payload or {})
        except StopIteration:
            self.complete = True
        return self.current

    def result(self) -> Character:
        return self.char

    # ---- helpers -------------------------------------------------------
    def _log(self, msg: str) -> None:
        self.feed.append(msg)
        self.char.log.append(msg)

    def _decision(self, step: str, **kw) -> Dict[str, Any]:
        d = {"step": step, "feed": list(self.feed), "character": self._snapshot()}
        d.update(kw)
        self.feed = []
        return d

    def _snapshot(self) -> Dict[str, Any]:
        c = self.char
        return {"name": c.name, "race": c.race,
                "class": "/".join(c.classes_list) if c.classes_list else c.char_class,
                "alignment": c.alignment, "scores": dict(c.scores),
                "str_pct": c.str_pct, "hp": c.hp_max, "gold": c.gold,
                "ac_descending": c.ac_descending, "ac_ascending": c.ac_ascending}

    # ---- the build (generator coroutine) ------------------------------
    def _script(self):
        c = self.char

        # 1) Ability scores: pick a method, then roll-and-assign (with unlimited
        #    rerolls) or input directly for hero/god-tier characters.
        ans = yield self._decision(
            "ability_method", options=["4d6", "5d6", "3d6", "input"],
            prompt="How should ability scores be generated?")
        method = (ans or {}).get("method", "4d6")

        if method == "input":
            ans = yield self._decision(
                "input_scores", abilities=list(ORDER),
                prompt="Enter the six ability scores.")
            given = (ans or {}).get("scores", {})
            scores = {a: int(given.get(a, 10)) for a in ORDER}
            self._log("Scores entered: {}".format(self._upp(scores)))
        else:
            roller = _METHOD_ROLLERS.get(method, _METHOD_ROLLERS["4d6"])
            while True:
                rolled = [roller(self.dice) for _ in range(6)]
                self._log("Rolled six scores ({}): {} (total {})".format(
                    method, rolled, sum(rolled)))
                ans = yield self._decision(
                    "assign_scores", rolled=rolled, slots=list(ORDER),
                    method=method, total=sum(rolled),
                    prompt="Assign each rolled value to an ability (or reroll).")
                if (ans or {}).get("reroll"):
                    self._log("Rerolled.")
                    continue
                scores = self._read_assignment(ans, rolled)
                break

        c.scores = scores
        self._log("Abilities set: {}".format(self._upp(scores)))

        # 2) Ancestry. Eligible = requirements met after adjustments (or all if
        #    overrides are on). Adjustments are then applied.
        eligible = [r for r in races_mod.RACES
                    if self.allow_overrides or self._race_ok(r, scores)]
        ans = yield self._decision(
            "choose_ancestry", options=eligible,
            prompt="Choose an ancestry.")
        race = (ans or {}).get("ancestry") or eligible[0]
        c.race = race
        self._apply_ancestry(race)

        # 3) Class. Allowed = the race's classes that meet minimums (or every
        #    class if overrides are on). Multi-class is always offered; under
        #    overrides (our "weird Greyhawk") ANY combination of ANY classes is
        #    legal -- no race gate, no two-/three-class limit, no like-class rule.
        if self.allow_overrides:
            options = list(classes_mod.CLASSES.keys())
        else:
            options = [cl for cl in races_mod.get(race).allowed_classes
                       if classes_mod.meets_minimums(cl, c.scores)]
            if not options:                       # bad rolls: offer with a note
                options = list(races_mod.get(race).allowed_classes)
                self._log("No class fully meets minimums; OSRIC's XP-penalty "
                          "rule would apply.")
        ans = yield self._decision(
            "choose_class", options=options, multi=True,
            prompt="Choose one class, or several to multi-class.")
        chosen = self._read_classes(ans, options)
        c.classes_list = chosen
        c.char_class = chosen[0]                   # primary drives derived tables
        if len(chosen) > 1:
            self._log("Multi-class: {}.".format("/".join(chosen)))
        else:
            self._log("Class: {}".format(chosen[0]))

        # 4) Alignment. Single class -> its allowed list. Multi-class -> the
        #    intersection (the alignments ALL classes permit); under overrides,
        #    or if that intersection is empty, offer every alignment.
        aligns = self._alignment_options(chosen)
        ans = yield self._decision(
            "choose_alignment", options=aligns,
            prompt="Choose an alignment.")
        c.alignment = (ans or {}).get("alignment") or aligns[0]
        self._log("Alignment: {}".format(c.alignment))

        # 5) Derived stats (no decisions): exceptional STR, HP, AC, gold, bonus.
        self._finish_derived()

        # 6) Name last, once the character has taken shape.
        ans = yield self._decision(
            "name_character", sheet=self.sheet(),
            prompt="Name your character.")
        chosen = (ans or {}).get("name")
        if chosen and str(chosen).strip():
            c.name = str(chosen).strip()

        self.complete = True
        yield self._decision("complete", sheet=self.sheet(),
                             prompt="Character complete.")

    # ---- mechanics -----------------------------------------------------
    def _read_assignment(self, ans, rolled) -> Dict[str, int]:
        a = (ans or {}).get("assignment")
        if isinstance(a, dict):
            return {k: int(a.get(k)) for k in ORDER}
        if isinstance(a, (list, tuple)) and len(a) == 6:
            return {ORDER[i]: int(a[i]) for i in range(6)}
        return {ORDER[i]: rolled[i] for i in range(6)}   # default: in order

    def _read_classes(self, ans, options) -> List[str]:
        """Accept {'classes': [...]} (multi) or {'class': 'X'} (single).

        Dedupes while preserving order. Under overrides any class is allowed;
        otherwise picks are filtered to the offered options (falling back to the
        first option if nothing valid was chosen).
        """
        ans = ans or {}
        picked = ans.get("classes")
        if not picked:
            one = ans.get("class")
            picked = [one] if one else []
        out: List[str] = []
        for cl in picked:
            if cl in classes_mod.CLASSES and cl not in out:
                if self.allow_overrides or cl in options:
                    out.append(cl)
        return out or [options[0]]

    def _alignment_options(self, chosen: List[str]) -> List[str]:
        if self.allow_overrides:
            return list(ALL_ALIGNMENTS)
        allowed = None
        for cl in chosen:
            s = set(classes_mod.get(cl).alignments)
            allowed = s if allowed is None else (allowed & s)
        allowed = allowed or set()
        # keep canonical order; if the classes share nothing, offer all nine.
        ordered = [a for a in ALL_ALIGNMENTS if a in allowed]
        return ordered or list(ALL_ALIGNMENTS)

    def _race_ok(self, race: str, scores: Dict[str, int]) -> bool:
        r = races_mod.get(race)
        for a in ORDER:
            lo, hi = r.requirements[a]
            adj = min(scores[a] + r.adjustments.get(a, 0), hi)
            if adj < lo:
                return False
        return True

    def _apply_ancestry(self, race: str) -> None:
        r = races_mod.get(race)
        for a in ORDER:
            lo, hi = r.requirements[a]
            self.char.scores[a] = max(lo, min(self.char.scores[a]
                                              + r.adjustments.get(a, 0), hi)) \
                if not self.allow_overrides else \
                min(self.char.scores[a] + r.adjustments.get(a, 0), hi)
        if r.adjustments:
            self._log("{} adjustments applied: {}".format(
                race, self._upp(self.char.scores)))

    def _finish_derived(self) -> None:
        c = self.char
        classes = c.classes_list or [c.char_class]
        cls = classes_mod.get(c.char_class)        # primary, for tables
        warrior = any(cl in WARRIORS for cl in classes)

        # Exceptional Strength: an 18 for a warrior rolls percentile.
        if warrior and c.scores.get("str") == 18:
            pct = self.dice.d100()
            if pct >= 100:
                c.scores["str"] = 19
                self._log("Exceptional Strength: rolled 00 -> Strength 19!")
            else:
                c.str_pct = pct
                self._log("Exceptional Strength: 18/{:02d}.".format(pct))

        # Hit points. Single class: its first-level HD + CON mod. Multi-class:
        # roll each class's HD and average them (1e style), then add CON mod.
        con_mod = ab.constitution_mods(c.scores["con"], warrior=warrior)["hp_mod"]
        if len(classes) == 1:
            dice_total = sum(self.dice.d(cls.hit_die) for _ in range(cls.first_level_hd))
            c.hp_max = max(1, dice_total + con_mod)
            self._log("Hit points: {}d{}{:+d} = {}.".format(
                cls.first_level_hd, cls.hit_die, con_mod, c.hp_max))
        else:
            rolls = []
            for cl in classes:
                k = classes_mod.get(cl)
                rolls.append(sum(self.dice.d(k.hit_die) for _ in range(k.first_level_hd)))
            avg = sum(rolls) // len(rolls)
            c.hp_max = max(1, avg + con_mod)
            self._log("Hit points (multi-class, averaged): rolls {} -> {} {:+d} = {}.".format(
                rolls, avg, con_mod, c.hp_max))

        # Armour class (unarmoured). Monks get no DEX bonus to AC.
        dex_ac = 0 if c.char_class == "Monk" else ab.dexterity_mods(c.scores["dex"])["ac_adj"]
        c.ac_descending = 10 + dex_ac
        c.ac_ascending = 20 - c.ac_descending

        # Starting gold. Multi-class: roll each class's funds, take the best.
        golds = []
        for cl in classes:
            k = classes_mod.get(cl)
            golds.append(self.dice.notation(k.gold_dice).total * k.gold_mult)
        c.gold = max(golds)
        self._log("Starting gold: {} gp.".format(c.gold))

        # Prime-requisite XP bonus: qualifies if ANY class's prime req is met.
        c.xp_bonus = any(classes_mod.xp_bonus(cl, c.scores) for cl in classes)
        if c.xp_bonus:
            self._log("Qualifies for the +10% prime-requisite XP bonus.")

    # ---- presentation --------------------------------------------------
    @staticmethod
    def _upp(scores: Dict[str, int]) -> str:
        return " ".join("{} {}".format(a.upper(), scores[a]) for a in ORDER)

    def sheet(self) -> str:
        c = self.char
        st = "{}{}".format(c.scores.get("str"),
                           "/{:02d}".format(c.str_pct) if c.str_pct else "")
        lines = [
            "{}".format(c.name),
            "{} {} ({})".format(
                c.race or "?",
                "/".join(c.classes_list) if c.classes_list else (c.char_class or "?"),
                c.alignment or "?"),
            "STR {}  DEX {}  CON {}  INT {}  WIS {}  CHA {}".format(
                st, c.scores.get("dex"), c.scores.get("con"),
                c.scores.get("int"), c.scores.get("wis"), c.scores.get("cha")),
            "HP {}   AC {} [asc {}]   Gold {} gp".format(
                c.hp_max, c.ac_descending, c.ac_ascending, c.gold),
        ]
        return "\n".join(lines)
