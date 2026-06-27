"""tools.py -- the tools the referee may call.

Each tool wraps the deterministic engine, the database, or the lookup oracles, so
the model narrates but never computes or remembers on its own. Every tool returns
plain JSON-able data. specs() yields the OpenAI tool schemas; dispatch() runs one.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from engine.dice import Dice
from engine import combat
from engine import initiative as init_mod
from engine import leveling as leveling_mod
from engine import thief_skills as thief_mod
from engine import turning as turning_mod
from engine import henchmen as hench_mod
from engine import encumbrance as enc_mod
from engine import conditions as cond_mod
from engine import specialization as spec_mod
from engine import magecraft as mage_mod
from engine.data import abilities as ab_mod
from engine import rules_lookup
from engine.data import classes as class_data
from engine.data import loyalty as loyalty_data
from engine.data import equipment as equip_data
from engine import spellcasting
from engine.data import saves as saves_mod
from engine.data import spells as spell_catalog
from engine.data import spell_effects as spell_fx
from engine.data import monsters as bestiary
from engine.data import treasure as treasure_mod
from engine.data import magic_items as magic_mod

# If a campaign was created without an in-game date, seed it here the first time
# any tool needs the date, so the calendar starts ticking and persists thereafter.
DEFAULT_START_DATE = "Longlight 1, 211 AS"
from engine.data import encounters as encounters_mod
from engine.data import weather as weather_mod
from engine import travel as travel_mod
from engine import trade as trade_mod
from engine import vessels as vessels_mod
from engine import domain as domain_mod
from engine import dominion_events as dom_events_mod
from engine import calendar as cal_mod
from engine import downtime as downtime_mod
from engine import exploration as explore_mod
from engine.data import proficiency as prof_mod
from engine import warmachine as war_mod
from engine import naval as naval_mod


class RefereeTools:
    def __init__(self, repo, campaign_id: int, dice: Optional[Dice] = None):
        self.repo = repo
        self.cid = campaign_id
        self.dice = dice or Dice()

    # ---- helpers -------------------------------------------------------
    def _find_char(self, name: str) -> Optional[Dict[str, Any]]:
        nl = (name or "").strip().lower()
        for r in self.repo.list_characters(self.cid):
            if r["name"].lower() == nl:
                return dict(r)
        return None

    @staticmethod
    def _class_level(row: Dict[str, Any]):
        cs = json.loads(row["classes_json"] or "[]")
        first = cs[0] if cs else {"class": "Fighter", "level": 1}
        return first.get("class", "Fighter"), int(first.get("level", 1))

    @staticmethod
    def _classes_full(row: Dict[str, Any]):
        cs = json.loads(row["classes_json"] or "[]")
        return cs or [{"class": "Fighter", "level": 1}]

    @staticmethod
    def _class_str(row: Dict[str, Any]) -> str:
        cs = json.loads(row["classes_json"] or "[]")
        return "/".join(str(c.get("class", "?")) for c in cs) or "Fighter"

    def _spell_slots(self, row: Dict[str, Any]):
        """Per-class available slots and USED counts. Each memorized spell is
        attributed to exactly one owning class by greedy replay (same rule
        memorize_spell uses), so a spell shared by two classes is never double-
        counted. Returns (avail{cls:[slots]}, used{cls:{level:n}})."""
        wis = row["wis_score"]
        avail = {}
        for c in self._classes_full(row):
            ccls = c.get("class"); clvl = int(c.get("level", 1))
            sl = spellcasting.available_slots(ccls, clvl, wis)
            if sl:
                avail[ccls] = sl
        used = {ccls: {} for ccls in avail}
        for nm in json.loads(row["memorized_json"] or "[]"):
            owners = [ccls for ccls in avail if spell_catalog.find(nm, ccls)]
            if not owners:
                continue
            placed = False
            for ccls in owners:
                sp = spell_catalog.find(nm, ccls)
                if (sp.level - 1 < len(avail[ccls])
                        and used[ccls].get(sp.level, 0) < avail[ccls][sp.level - 1]):
                    used[ccls][sp.level] = used[ccls].get(sp.level, 0) + 1
                    placed = True; break
            if not placed:                       # overfull -- count vs first owner
                sp = spell_catalog.find(nm, owners[0])
                used[owners[0]][sp.level] = used[owners[0]].get(sp.level, 0) + 1
        return avail, used

    # ---- tools ---------------------------------------------------------
    def roll_dice(self, notation: str) -> Dict[str, Any]:
        r = self.dice.notation(notation)
        return {"notation": notation, "dice": r.dice, "total": r.total}

    def lookup_rule(self, query: str) -> Dict[str, Any]:
        return {"query": query, "source": "OSRIC (authoritative)",
                "results": rules_lookup.rules(query, limit=4)}

    def lookup_lore(self, query: str) -> Dict[str, Any]:
        return {"query": query, "source": "1e reference corpus (supplementary)",
                "results": rules_lookup.lore(query, limit=4)}

    def list_characters(self) -> Dict[str, Any]:
        out = []
        for r in self.repo.list_characters(self.cid):
            rd = dict(r)
            cls, lvl = self._class_level(rd)
            out.append({"name": r["name"], "race": r["race"],
                        "class": self._class_str(rd),
                        "classes": [{"class": c.get("class"), "level": c.get("level", 1)}
                                    for c in self._classes_full(rd)],
                        "level": lvl, "alignment": r["alignment"],
                        "hp": r["hp_current"], "hp_max": r["hp_max"],
                        "ac": r["ac_descending"], "alive": bool(r["alive"]),
                        "is_npc": bool(r["is_npc"])})
        return {"characters": out}

    def get_character(self, name: str) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        cls, lvl = self._class_level(row)
        return {"name": row["name"], "race": row["race"],
                "class": self._class_str(row),
                "classes": [{"class": c.get("class"), "level": c.get("level", 1)}
                            for c in self._classes_full(row)],
                "level": lvl,
                "alignment": row["alignment"],
                "str": row["str_score"], "str_pct": row["str_pct"],
                "dex": row["dex_score"], "con": row["con_score"],
                "int": row["int_score"], "wis": row["wis_score"], "cha": row["cha_score"],
                "hp": row["hp_current"], "hp_max": row["hp_max"],
                "ac": row["ac_descending"], "gold": row["gold"],
                "gear": json.loads(row["gear_json"] or "[]"),
                "memorized": json.loads(row["memorized_json"] or "[]"),
                "alive": bool(row["alive"]), "status": row["status"]}

    def saving_throw(self, name: str, category: str,
                     modifier: int = 0) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        classes = json.loads(row["classes_json"] or "[]")
        return combat.saving_throw_classes(self.dice, classes, category, modifier)

    def _is_large(self, row: Dict[str, Any], override: Optional[str] = None) -> bool:
        """Is the defender Large or bigger (so weapons use their 'vs L+' damage)?"""
        size = override
        if size is None and row.get("is_npc") and row.get("race"):
            m = bestiary.get(row["race"])
            size = m.size if m else None
        s = (size or "medium").lower()
        return any(k in s for k in ("large", "huge", "giant", "gigantic",
                                    "gargantuan", "colossal"))

    def attack(self, attacker: str, defender: str, situational: int = 0,
               damage_dice: str = "1d6", weapon: Optional[str] = None,
               defender_size: Optional[str] = None) -> Dict[str, Any]:
        _, err = self._require_turn(attacker)
        if err:
            return err
        a, d = self._find_char(attacker), self._find_char(defender)
        if not a or not d:
            return {"error": "attacker or defender not found"}
        spec_info = None
        nonprof_penalty = None
        vs_large = self._is_large(dict(d), defender_size)
        if weapon:                              # named weapon: use catalog damage
            wpn = equip_data.lookup(weapon)
            if wpn and wpn["category"] in ("weapon", "ammunition"):
                # damage vs Large+ targets uses the weapon's L+ column
                damage_dice = (wpn.get("damage_lg") if vs_large else None) \
                    or wpn.get("damage_sm", damage_dice)
                spec = json.loads(a["specialization_json"] or "null") \
                    if "specialization_json" in a.keys() and a["specialization_json"] else None
                _, lvl = self._class_level(dict(a))
                is_missile = bool(wpn.get("launched") or wpn.get("range"))
                spec_info = spec_mod.assess(spec, wpn["name"], lvl, is_missile)
                # Non-proficiency penalty: only if a proficiency list is set and
                # this weapon isn't on it.
                prof = json.loads(a["proficiencies_json"] or "null") \
                    if "proficiencies_json" in a.keys() and a["proficiencies_json"] else None
                if prof is not None and wpn["name"] not in prof:
                    nonprof_penalty = prof_mod.best_penalty(
                        json.loads(a["classes_json"] or "[]"))
                    situational += nonprof_penalty
        ca = combat.combatant_from_row(a, damage_dice=damage_dice)
        cd = combat.combatant_from_row(d)
        if spec_info:                           # +1 to hit, +2 (or +3) damage
            situational += spec_info["to_hit"]
            ca.damage_mod += spec_info["damage"]
        result = combat.resolve_attack(ca, cd, self.dice, situational=situational)
        if weapon:
            result["weapon"] = weapon
            result["vs_large"] = vs_large
            if nonprof_penalty is not None:
                result["non_proficiency_penalty"] = nonprof_penalty
        # Attack rate: specialisation replaces the base class progression.
        cb = self.repo.active_combat(self.cid)
        rnd = cb["round"] if cb else 1
        if spec_info:
            result["specialised"] = True
            rate = spec_info["attack_rate"]
        else:
            rate = spec_mod.best_base_rate(json.loads(a["classes_json"] or "[]"))
        result["attack_rate"] = rate
        result["attacks_this_round"] = spec_mod.attacks_this_round(rate, rnd)
        # Persist the defender's new HP / status (death's door for PCs).
        took_damage = result.get("damage", 0) > 0
        state = self._write_hp(d, cd.hp, from_damage=took_damage)
        result["defender_status"] = state["status"]
        result["defender_down"] = state["hp"] <= 0
        snap = self._mark_acted(attacker)        # this was the attacker's action
        if snap:
            result["combat"] = snap
        return result

    def set_weapon_specialisation(self, name: str, weapon: str,
                                  double: bool = False) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        cls, lvl = self._class_level(dict(row))
        classes = json.loads(row["classes_json"] or "[]")
        if not any(spec_mod.can_specialise(c.get("class")) for c in classes):
            return {"error": "only fighters, rangers, and paladins may specialise"}
        wpn = equip_data.lookup(weapon)
        if not wpn or wpn["category"] != "weapon":
            return {"error": "no such weapon: {}".format(weapon)}
        spec = {"weapon": wpn["name"], "double": bool(double)}
        self.repo.conn.execute(
            "UPDATE character SET specialization_json=? WHERE id=?",
            (json.dumps(spec), row["id"]))
        self.repo.conn.commit()
        b = spec_mod.bonuses(bool(double) and wpn["name"] not in spec_mod.NO_DOUBLE)
        return {"name": name, "weapon": wpn["name"], "double": spec["double"],
                "to_hit": b["to_hit"], "damage": b["damage"],
                "attack_rate": spec_mod.melee_attack_rate(lvl)}

    def dual_class(self, name: str, to_class: str) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        if (row["race"] or "") != "Human":
            return {"error": "only humans may dual-class"}
        if to_class not in class_data.CLASSES:
            return {"error": "unknown class: {}".format(to_class)}
        classes = json.loads(row["classes_json"] or "[]")
        if len(classes) != 1:
            return {"error": "dual-classing requires a single-classed character"}
        from_class = classes[0]["class"]
        from_level = int(classes[0].get("level", 1))
        if to_class == from_class:
            return {"error": "already a {}".format(to_class)}
        scores = self._scores(dict(row))
        # >=15 in the old class's prime req(s); >=17 in the new class's.
        for req in class_data.get(from_class).prime_requisites:
            if (scores.get(req) or 0) < 15:
                return {"error": "need 15+ {} to leave {}".format(req.upper(), from_class)}
        for req in class_data.get(to_class).prime_requisites:
            if (scores.get(req) or 0) < 17:
                return {"error": "need 17+ {} to become a {}".format(req.upper(), to_class)}
        new_classes = [
            {"class": from_class, "level": from_level,
             "xp": classes[0].get("xp", 0), "suppressed": True},
            {"class": to_class, "level": 1, "xp": 0},
        ]
        dual = {"from": from_class, "from_level": from_level, "to": to_class}
        self.repo.conn.execute(
            "UPDATE character SET classes_json=?, dual_class_json=? WHERE id=?",
            (json.dumps(new_classes), json.dumps(dual), row["id"]))
        self.repo.conn.commit()
        self.repo.record_event(
            self.cid, "level", "{} began dual-classing from {} {} to {}.".format(
                name, from_class, from_level, to_class), in_game_date=self._date())
        return {"name": name, "from": from_class, "from_level": from_level,
                "to": to_class, "note": "All XP now goes to {}; old class "
                "abilities return once you exceed {} {}.".format(
                    to_class, from_class, from_level)}

    def set_hp(self, name: str, hp_current: int,
               hp_max: Optional[int] = None,
               status: Optional[str] = None) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        # Allow setting the maximum too -- needed for familiar bonuses, temporary
        # hit points, level drain, etc. Stored max caps later healing correctly.
        if hp_max is not None:
            self.repo.conn.execute(
                "UPDATE character SET hp_max=? WHERE id=?",
                (int(hp_max), row["id"]))
            self.repo.conn.commit()
            row = self._find_char(name)          # refresh so _write_hp sees new max
        state = self._write_hp(row, hp_current, explicit_status=status)
        out = {"name": name, **state}
        if hp_max is not None:
            out["hp_max"] = int(hp_max)
        return out

    # ---- experience & advancement -------------------------------------
    def _scores(self, row: Dict[str, Any]) -> Dict[str, int]:
        return {"str": row["str_score"], "dex": row["dex_score"],
                "con": row["con_score"], "int": row["int_score"],
                "wis": row["wis_score"], "cha": row["cha_score"]}

    def _grant_one(self, row: Dict[str, Any], amount: int) -> Dict[str, Any]:
        classes = json.loads(row["classes_json"] or "[]")
        scores = self._scores(row)
        dual = json.loads(row["dual_class_json"] or "null") \
            if "dual_class_json" in row.keys() and row["dual_class_json"] else None
        camp = self.repo.get_campaign(self.cid)
        training = bool(camp["training_required"]) if camp and "training_required" in camp.keys() else False
        if training and not dual:                # XP banks; level only on training
            banked = leveling_mod.bank_xp(
                classes, int(amount),
                prime_bonus=any(class_data.xp_bonus(c.get("class"), scores)
                                for c in classes if c.get("class") in class_data.CLASSES))
            self.repo.conn.execute("UPDATE character SET classes_json=? WHERE id=?",
                                   (json.dumps(banked["classes"]), row["id"]))
            self.repo.conn.commit()
            return {"name": row["name"], "xp_each": banked["xp_each"],
                    "ready_to_train": banked["ready_to_train"], "level_ups": [],
                    "hp_gained": 0,
                    "classes": [{"class": c["class"], "level": c["level"],
                                 "xp": c["xp"]} for c in banked["classes"]]}
        if dual:                                # all XP to the new class
            res = leveling_mod.grant_xp_dual(
                self.dice, classes, int(amount), int(scores.get("con") or 10),
                dual["from"], int(dual["from_level"]), dual["to"])
            res["xp_each"] = int(amount)
        else:
            prime = any(class_data.xp_bonus(c.get("class"), scores)
                        for c in classes if c.get("class") in class_data.CLASSES)
            res = leveling_mod.grant_xp(self.dice, classes, int(amount),
                                        int(scores.get("con") or 10), prime_bonus=prime)
        new_hp_max = (row["hp_max"] or 0) + res["hp_gained"]
        new_hp_cur = (row["hp_current"] if row["hp_current"] is not None
                      else row["hp_max"] or 0) + res["hp_gained"]
        self.repo.conn.execute(
            "UPDATE character SET classes_json=?, hp_max=?, hp_current=? WHERE id=?",
            (json.dumps(res["classes"]), new_hp_max, new_hp_cur, row["id"]))
        self.repo.conn.commit()
        for lv in res["level_ups"]:
            self.repo.record_event(
                self.cid, "level",
                "{} reached {} level {} (was {}).".format(
                    row["name"], lv["class"], lv["to"], lv["from"]),
                in_game_date=self._date())
        return {"name": row["name"], "xp_each": res["xp_each"],
                "hp_gained": res["hp_gained"], "hp_max": new_hp_max,
                "level_ups": res["level_ups"],
                "classes": [{"class": c["class"], "level": c["level"],
                             "xp": c["xp"]} for c in res["classes"]]}

    def grant_xp(self, amount: int, name: Optional[str] = None) -> Dict[str, Any]:
        """Award XP to one named character, or split a party award: pass no name
        to give `amount` to every player character (each gets the full amount --
        the classic 'XP per head' share you've already divided)."""
        if name:
            row = self._find_char(name)
            if not row:
                return {"error": "no character named {}".format(name)}
            return self._grant_one(dict(row), amount)
        out = []
        for r in self.repo.list_characters(self.cid, include_npcs=False):
            out.append(self._grant_one(dict(r), amount))
        return {"awarded": int(amount), "characters": out}

    def get_advancement(self, name: str) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        classes = json.loads(row["classes_json"] or "[]")
        return {"name": name,
                "effective_level": leveling_mod.effective_level(
                    leveling_mod.normalize(classes)),
                "classes": leveling_mod.xp_to_next(classes)}

    def set_training_required(self, on: bool = True) -> Dict[str, Any]:
        """Toggle whether gaining a level requires training (time + gold). When
        on, grant_xp banks XP and the character must train to level up."""
        self.repo.set_training_required(self.cid, bool(on))
        return {"training_required": bool(on)}

    def train(self, name: str, char_class: Optional[str] = None) -> Dict[str, Any]:
        """Train up one level (the XP must already be earned): rolls the new
        level's hit points, charges 1,500 gp x current level, and advances the
        calendar 1d3 weeks."""
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        classes = json.loads(row["classes_json"] or "[]")
        ready = leveling_mod.bank_xp(classes, 0)["ready_to_train"]
        if not ready:
            return {"name": name, "note": "no level is ready to train"}
        cls = char_class or ready[0]["class"]
        con = (row["con_score"] or 10)
        res = leveling_mod.train(self.dice, classes, cls, int(con))
        if "error" in res:
            return res
        cost = downtime_mod.training_cost(res["from"])
        if (row["gold"] or 0) < cost:
            return {"error": "not enough gold to train", "cost_gp": cost,
                    "gold": row["gold"] or 0}
        weeks = self.dice.d(3)
        new_hp_max = (row["hp_max"] or 0) + res["hp_gained"]
        new_hp_cur = (row["hp_current"] if row["hp_current"] is not None
                      else row["hp_max"] or 0) + res["hp_gained"]
        self.repo.conn.execute(
            "UPDATE character SET classes_json=?, hp_max=?, hp_current=?, gold=? "
            "WHERE id=?",
            (json.dumps(res["classes"]), new_hp_max, new_hp_cur,
             (row["gold"] or 0) - cost, row["id"]))
        self.repo.conn.commit()
        new_date = self._advance_calendar(weeks * 7)
        self.repo.record_event(
            self.cid, "level", "{} trained to {} level {} ({} weeks, {} gp).".format(
                name, res["class"], res["to"], weeks, cost), in_game_date=new_date)
        return {"name": name, "class": res["class"], "to": res["to"],
                "hp_gained": res["hp_gained"], "cost_gp": cost,
                "weeks": weeks, "hp_max": new_hp_max, "date": new_date}

    # ---- time, rest & natural healing ---------------------------------
    def _advance_calendar(self, days: int) -> Optional[str]:
        camp = self.repo.get_campaign(self.cid)
        cur = (camp["current_date"] if camp else None) or DEFAULT_START_DATE
        if cal_mod.parse(cur) is None:           # heal a leaked real-world date
            cur = DEFAULT_START_DATE
        new = cal_mod.advance(cur, int(days)) or cur
        if new:
            self.repo.set_date(self.cid, new)
        return new

    def advance_time(self, days: int) -> Dict[str, Any]:
        """Move the campaign calendar forward by `days` and report the new date."""
        new = self._advance_calendar(int(days))
        return {"days": int(days), "date": new}

    def rest(self, days: int, name: Optional[str] = None) -> Dict[str, Any]:
        """Rest for `days`: advance the calendar and apply natural healing (1 hp/
        day, Constitution-adjusted; four weeks restores full). With a name, just
        that character rests; otherwise the whole party does."""
        new_date = self._advance_calendar(int(days))
        targets = ([self._find_char(name)] if name
                   else self.repo.list_characters(self.cid, include_npcs=False))
        healed = []
        for r in targets:
            if not r:
                continue
            if r["alive"] == 0 or (r["hp_current"] or 0) <= 0:
                continue                          # the dead and dying don't heal by rest
            h = downtime_mod.natural_healing(int(days), r["hp_current"] or 0,
                                             r["hp_max"] or 0, r["con_score"] or 10)
            if h["healed"]:
                self.repo.conn.execute(
                    "UPDATE character SET hp_current=? WHERE id=?", (h["hp"], r["id"]))
                self.repo.conn.commit()
            healed.append({"name": r["name"], "healed": h["healed"], "hp": h["hp"]})
            # A full night's rest clears prepared spells, so a caster re-prays /
            # re-studies a fresh loadout each day. This is what makes the standing
            # dawn-refresh rule work: after rest, the slots are empty to fill anew.
            if int(days) >= 1:
                self.repo.conn.execute(
                    "UPDATE character SET memorized_json='[]' WHERE id=?", (r["id"],))
                self.repo.conn.commit()
        return {"days": int(days), "date": new_date, "rested": healed}

    # ---- weapon proficiency & exploration -----------------------------
    def set_proficiencies(self, name: str, weapons: List[str]) -> Dict[str, Any]:
        """Set a character's proficient weapons. Once set, attacking with a weapon
        not on the list takes the class non-proficiency penalty."""
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        canon = []
        for w in weapons or []:
            found = equip_data.lookup(w)
            canon.append(found["name"] if found and found["category"] == "weapon" else w)
        self.repo.conn.execute("UPDATE character SET proficiencies_json=? WHERE id=?",
                               (json.dumps(canon), row["id"]))
        self.repo.conn.commit()
        cls, lvl = self._class_level(dict(row))
        return {"name": name, "proficient": canon,
                "slots": prof_mod.slots(cls, lvl),
                "non_proficiency_penalty": prof_mod.best_penalty(
                    json.loads(row["classes_json"] or "[]"))}

    def proficiency_slots(self, name: str) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        out = []
        for c in json.loads(row["classes_json"] or "[]"):
            out.append({"class": c.get("class"),
                        "slots": prof_mod.slots(c.get("class"), int(c.get("level", 1)))})
        prof = json.loads(row["proficiencies_json"] or "null")
        return {"name": name, "by_class": out, "proficient": prof or []}

    def _race_of(self, name: str) -> str:
        r = self._find_char(name)
        return (r["race"] if r else "Human") or "Human"

    def search(self, name: str, what: str = "secret doors") -> Dict[str, Any]:
        """Search a 10ft area: 'secret doors' (1 in 6, elves 2 in 6) or 'traps'
        (2 in 6, dwarves/gnomes 3 in 6). Thieves should use thief_skill for traps."""
        race = self._race_of(name)
        if "trap" in what.lower():
            res = explore_mod.search_traps(self.dice, race)
        else:
            res = explore_mod.search_secret_doors(self.dice, race)
        res["name"] = name
        return res

    def listen_at_door(self, name: str) -> Dict[str, Any]:
        res = explore_mod.listen_at_door(self.dice, self._race_of(name))
        res["name"] = name
        return res

    def force_door(self, name: str) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        res = explore_mod.force_door(self.dice, row["str_score"] or 10,
                                     row["str_pct"] or 0)
        res["name"] = name
        return res

    def bend_bars(self, name: str) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        res = explore_mod.bend_bars(self.dice, row["str_score"] or 10,
                                    row["str_pct"] or 0)
        res["name"] = name
        return res

    def surprise_check(self, party: Optional[List[str]] = None,
                       foe_dex: int = 10, foe_surprises_on: int = 2) -> Dict[str, Any]:
        """Roll surprise for both sides. Pass the party's names (their best
        Dexterity is used); foe_surprises_on raises the foes' surprise threshold "
        "(e.g. 3 for a stealthy monster)."""
        best = 10
        for n in (party or []):
            r = self._find_char(n)
            if r and (r["dex_score"] or 0) > best:
                best = r["dex_score"]
        return explore_mod.surprise(self.dice, best, int(foe_dex),
                                    int(foe_surprises_on))

    def light_duration(self, source: str) -> Dict[str, Any]:
        return {"source": source, **explore_mod.light_duration(source)}

    # ---- class identity: thief skills & turning undead ----------------
    def thief_skill(self, name: str, skill: str,
                    modifier: int = 0) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        classes = json.loads(row["classes_json"] or "[]")
        lvl = thief_mod.thief_level(classes)
        if lvl is None:
            return {"error": "{} has no thief or assassin levels".format(name)}
        res = thief_mod.check(self.dice, skill, lvl, row["dex_score"] or 10,
                              row["race"] or "", modifier)
        res["name"] = name
        return res

    def turn_undead(self, name: str, undead: str,
                    number: Optional[int] = None) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        classes = json.loads(row["classes_json"] or "[]")
        turner = None
        for c in classes:
            if c.get("class") in ("Cleric", "Paladin"):
                # prefer a Cleric; otherwise take the paladin
                if turner is None or c.get("class") == "Cleric":
                    turner = c
        if not turner:
            return {"error": "{} cannot turn undead (not a cleric or paladin)".format(name)}
        eff = turning_mod.turning_level(turner["class"], int(turner.get("level", 1)))
        res = turning_mod.turn_undead(self.dice, eff, undead,
                                      alignment=row["alignment"] or "N",
                                      number_present=number)
        res["name"] = name
        if "error" not in res:
            self.repo.record_event(
                self.cid, "turning",
                "{} ({} as cleric {}) vs {}: {} ({} affected).".format(
                    name, turner["class"], eff, res.get("example"),
                    res.get("outcome"), res.get("affected", 0)),
                in_game_date=self._date())
        return res

    # ---- hirelings, henchmen & loyalty --------------------------------
    _FACTORS = ("status", "relationship", "service", "training", "payment",
                "treatment", "discipline")

    def _retainer_loyalty(self, ret: Dict[str, Any]) -> Dict[str, Any]:
        master = self._find_char(ret["master"])
        cha = (master["cha_score"] if master else 10) or 10
        align = (master["alignment"] if master else "N") or "N"
        return hench_mod.compute_loyalty(
            cha, alignment=align,
            relationship=ret["relationship"], status=ret["status"],
            service=ret["service"], training=ret["training"],
            payment=ret["payment"], treatment=ret["treatment"],
            discipline=ret["discipline"])

    def hire_henchman(self, master: str, name: str, race: str = "Human",
                      char_class: str = "Fighter", level: int = 1, hp: int = 6,
                      status: str = "henchman", **factors) -> Dict[str, Any]:
        m = self._find_char(master)
        if not m:
            return {"error": "no master named {}".format(master)}
        limit = loyalty_data.max_henchmen(m["cha_score"] or 10)
        current = len([r for r in self.repo.list_retainers(self.cid, master)
                       if r["status"] == "henchman"])
        warn = None
        if status == "henchman" and current >= limit:
            warn = ("{} already has {} henchmen (Charisma limit {}).".format(
                master, current, limit))
        chid = self.repo.save_character(self.cid, {
            "name": name, "race": race,
            "classes": [{"class": char_class, "level": int(level), "xp": 0}],
            "alignment": factors.get("alignment", m["alignment"] or "N"),
            "str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10,
            "hp_max": int(hp), "hp_current": int(hp), "ac_descending": 10,
            "notes": "{} to {}.".format(status.capitalize(), master),
        }, is_npc=True)
        fac = {k: factors[k] for k in self._FACTORS if k in factors}
        rid = self.repo.add_retainer(self.cid, chid, master, status=status, **fac)
        ret = dict(self.repo.get_retainer_by_character(chid))
        loy = self._retainer_loyalty(ret)
        self.repo.record_event(
            self.cid, "retainer", "{} took {} ({} {}) into service as a {}.".format(
                master, name, race, char_class, status),
            in_game_date=self._date())
        out = {"retainer_id": rid, "character_id": chid, "name": name,
               "master": master, "status": status,
               "loyalty": loy["loyalty"], "band": loy["band"],
               "henchman_limit": limit}
        if warn:
            out["warning"] = warn
        return out

    def list_henchmen(self, master: Optional[str] = None) -> Dict[str, Any]:
        out = []
        for r in self.repo.list_retainers(self.cid, master):
            ch = self.repo.get_character(r["character_id"]) if r["character_id"] else None
            loy = self._retainer_loyalty(dict(r))
            out.append({
                "name": ch["name"] if ch else "?", "master": r["master"],
                "status": r["status"], "loyalty": loy["loyalty"],
                "band": loy["band"],
                "hp": ch["hp_current"] if ch else None,
                "alive": bool(ch["alive"]) if ch else None})
        return {"retainers": out}

    def loyalty_check(self, name: str, situational: int = 0) -> Dict[str, Any]:
        ch = self._find_char(name)
        if not ch:
            return {"error": "no character named {}".format(name)}
        ret = self.repo.get_retainer_by_character(ch["id"])
        if not ret:
            return {"error": "{} is not a hireling or henchman".format(name)}
        loy = self._retainer_loyalty(dict(ret))
        res = hench_mod.loyalty_test(self.dice, loy["loyalty"] + int(situational))
        res.update({"name": name, "band": loy["band"], "factors": loy["factors"]})
        self.repo.record_event(
            self.cid, "loyalty", "{} loyalty test ({}): {}.".format(
                name, loy["loyalty"] + int(situational),
                "holds" if res["holds"] else "wavers"),
            in_game_date=self._date())
        return res

    def set_retainer(self, name: str, **factors) -> Dict[str, Any]:
        ch = self._find_char(name)
        if not ch:
            return {"error": "no character named {}".format(name)}
        ret = self.repo.get_retainer_by_character(ch["id"])
        if not ret:
            return {"error": "{} is not a hireling or henchman".format(name)}
        updates = {k: factors[k] for k in self._FACTORS if k in factors}
        self.repo.update_retainer(ret["id"], **updates)
        new = dict(self.repo.get_retainer_by_character(ch["id"]))
        loy = self._retainer_loyalty(new)
        return {"name": name, "updated": updates, "loyalty": loy["loyalty"],
                "band": loy["band"]}

    def reaction_roll(self, negotiator: Optional[str] = None,
                      situational: int = 0) -> Dict[str, Any]:
        mod = 0
        if negotiator:
            pc = self._find_char(negotiator)
            if pc:
                mod = loyalty_data.reaction_modifier(pc["cha_score"] or 10)
        res = hench_mod.reaction_roll(self.dice, mod, situational)
        res["negotiator"] = negotiator
        return res

    def npc_morale(self, name: str, situational: int = 0) -> Dict[str, Any]:
        ch = self._find_char(name)
        if not ch:
            return {"error": "no character named {}".format(name)}
        cls, lvl = self._class_level(dict(ch))
        loy_mod = 0
        ret = self.repo.get_retainer_by_character(ch["id"])
        if ret:
            master = self._find_char(ret["master"])
            if master:
                loy_mod = loyalty_data.loyalty_modifier(master["cha_score"] or 10)
        res = hench_mod.npc_morale(self.dice, lvl, loyalty_mod=loy_mod,
                                   situational=int(situational))
        res["name"] = name
        return res

    def spend_gold(self, name: str, amount: int) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        have = row["gold"] or 0
        if amount > have:
            return {"error": "not enough gold", "gold": have, "needed": amount}
        new = have - int(amount)
        self.repo.conn.execute("UPDATE character SET gold=? WHERE id=?",
                               (new, row["id"]))
        self.repo.conn.commit()
        return {"name": name, "spent": int(amount), "gold": new}

    def set_gold(self, name: str, amount: int) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        self.repo.conn.execute("UPDATE character SET gold=? WHERE id=?",
                               (int(amount), row["id"]))
        self.repo.conn.commit()
        return {"name": name, "gold": int(amount)}

    def add_gear(self, name: str, item: str) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        gear = json.loads(row["gear_json"] or "[]")
        gear.append(item)
        self.repo.conn.execute("UPDATE character SET gear_json=? WHERE id=?",
                               (json.dumps(gear), row["id"]))
        self.repo.conn.commit()
        return {"name": name, "added": item, "gear": gear}

    def remove_gear(self, name: str, item: str) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        gear = json.loads(row["gear_json"] or "[]")
        for i, g in enumerate(gear):
            label = g.get("item") if isinstance(g, dict) else g
            if str(label).lower() == item.lower():
                del gear[i]
                break
        self.repo.conn.execute("UPDATE character SET gear_json=? WHERE id=?",
                               (json.dumps(gear), row["id"]))
        self.repo.conn.commit()
        return {"name": name, "removed": item, "gear": gear}

    # ---- equipment catalog & encumbrance ------------------------------
    def list_equipment(self, category: Optional[str] = None) -> Dict[str, Any]:
        def fmt(table):
            out = []
            for nm, v in table.items():
                e = {"name": nm, "weight": v.get("weight"),
                     "cost": equip_data.cost_string(v["cost_cp"]) if v.get("cost_cp") is not None else "not sold"}
                if "damage_sm" in v:
                    e["damage"] = v["damage_sm"]
                    if v.get("range"):
                        e["range"] = v["range"]
                if "ac_desc" in v:
                    e["ac"] = "{} [{}]".format(v["ac_desc"], v["ac_asc"])
                elif "ac_bonus" in v:
                    e["ac"] = "+{} bonus".format(v["ac_bonus"])
                out.append(e)
            return out
        cat = (category or "").strip().lower()
        cats = {"weapon": equip_data.WEAPONS, "weapons": equip_data.WEAPONS,
                "armour": equip_data.ARMOUR, "armor": equip_data.ARMOUR,
                "gear": equip_data.GEAR, "ammunition": equip_data.AMMUNITION,
                "ammo": equip_data.AMMUNITION}
        if cat in cats:
            return {"category": cat, "items": fmt(cats[cat])}
        return {"weapons": fmt(equip_data.WEAPONS), "armour": fmt(equip_data.ARMOUR),
                "gear": fmt(equip_data.GEAR), "ammunition": fmt(equip_data.AMMUNITION)}

    def add_equipment(self, name: str, item: str, qty: int = 1,
                      pay: bool = False) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        found = equip_data.lookup(item)
        if not found:
            return {"error": "no catalog item named {}".format(item)}
        qty = max(1, int(qty))
        entry = {"item": found["name"], "qty": qty,
                 "weight": found.get("weight", 0) or 0}
        result = {"name": name, "added": found["name"], "qty": qty,
                  "unit_weight": entry["weight"],
                  "category": found["category"]}
        # Optional payment (gold is whole-gp, so sub-gp totals round up).
        if pay and found.get("cost_cp") is not None:
            total_cp = found["cost_cp"] * qty
            charge = (total_cp + 99) // 100          # ceil to whole gp
            have = row["gold"] or 0
            if charge > have:
                return {"error": "not enough gold", "gold": have,
                        "needed_gp": charge,
                        "cost": equip_data.cost_string(total_cp)}
            self.repo.conn.execute("UPDATE character SET gold=? WHERE id=?",
                                   (have - charge, row["id"]))
            result["charged_gp"] = charge
            result["cost"] = equip_data.cost_string(total_cp)
            result["gold"] = have - charge
        gear = json.loads(row["gear_json"] or "[]")
        gear.append(entry)
        self.repo.conn.execute("UPDATE character SET gear_json=? WHERE id=?",
                               (json.dumps(gear), row["id"]))
        self.repo.conn.commit()
        if found["category"] == "armour":
            ac = self.recalc_ac(name)
            if isinstance(ac, dict) and "ac_descending" in ac:
                result["ac_descending"] = ac["ac_descending"]
        return result

    def recalc_ac(self, name: str) -> Dict[str, Any]:
        """Recompute and store a character's AC from worn armour + shield + DEX,
        using the engine's own equipment and ability data. add_equipment calls
        this automatically whenever armour or a shield is added."""
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        gear = json.loads(row.get("gear_json") or "[]")
        classes = [c.get("class") for c in json.loads(row.get("classes_json") or "[]")]
        dex = row.get("dex_score") or 10
        dex_ac = 0 if "Monk" in classes else ab_mod.dexterity_mods(dex).get("ac_adj", 0)
        armours = [equip_data.ARMOUR[g["item"]]["ac_desc"] for g in gear
                   if g.get("item") in equip_data.ARMOUR
                   and "ac_desc" in equip_data.ARMOUR[g["item"]]]
        shields = [equip_data.ARMOUR[g["item"]]["ac_bonus"] for g in gear
                   if g.get("item") in equip_data.ARMOUR
                   and "ac_bonus" in equip_data.ARMOUR[g["item"]]]
        base = min(armours) if armours else 10
        shield = max(shields) if shields else 0
        ac_desc = base + dex_ac - shield
        ac_asc = 20 - ac_desc
        self.repo.conn.execute(
            "UPDATE character SET ac_descending=?, ac_ascending=? WHERE id=?",
            (ac_desc, ac_asc, row["id"]))
        self.repo.conn.commit()
        return {"name": name, "ac_descending": ac_desc, "ac_ascending": ac_asc,
                "armour_base": base, "shield_bonus": shield, "dex_adj": dex_ac}

    def encumbrance(self, name: str) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        gear = json.loads(row["gear_json"] or "[]")
        res = enc_mod.assess(gear, row["gold"] or 0, row["str_score"] or 10,
                             row["str_pct"] or 0, row["race"] or "Human")
        res["name"] = name
        return res

    # ---- combat conditions --------------------------------------------
    def _death_save_target(self, row: Dict[str, Any]) -> int:
        classes = json.loads(row["classes_json"] or "[]")
        norm = leveling_mod.normalize(classes)
        if norm:
            return leveling_mod.best_save_target(norm, "death")
        return saves_mod.save_target("Fighter", 1, "death")

    def poison_save(self, name: str, modifier: int = 0,
                    on_fail_damage: Optional[str] = None,
                    on_success_damage: Optional[str] = None) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        target = self._death_save_target(dict(row))
        res = cond_mod.poison_save(self.dice, target, int(modifier),
                                   on_fail_damage, on_success_damage)
        res["name"] = name
        if res["result"] == "dead":
            self.repo.conn.execute(
                "UPDATE character SET alive=0, status='dead', hp_current=0 WHERE id=?",
                (row["id"],))
            self.repo.conn.commit()
        elif res.get("damage"):
            self._apply_damage(dict(row), res["damage"])
        self.repo.record_event(
            self.cid, "poison", "{} saves vs poison ({}): {}.".format(
                name, target, res["result"]), in_game_date=self._date())
        return res

    def disease_check(self, name: str, modifier: int = 0,
                      in_hours: bool = False) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        target = self._death_save_target(dict(row))
        res = cond_mod.disease_check(self.dice, target, int(modifier), bool(in_hours))
        res["name"] = name
        self.repo.record_event(
            self.cid, "disease", "{} vs disease: {}.".format(
                name, "resisted" if res["saved"] else "contracted"),
            in_game_date=self._date())
        return res

    def drain_level(self, name: str, levels: int = 1) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        classes = json.loads(row["classes_json"] or "[]")
        old_total = sum(int(c.get("level", 1)) for c in
                        leveling_mod.normalize(classes)) or 1
        res = cond_mod.drain_levels(classes, int(levels))
        new_total = sum(c["level"] for c in res["classes"]) if res["classes"] else 0
        if res["slain"] or new_total <= 0:
            self.repo.conn.execute(
                "UPDATE character SET alive=0, status='dead', hp_current=0, "
                "classes_json=? WHERE id=?",
                (json.dumps(res["classes"]), row["id"]))
            self.repo.conn.commit()
            res["name"] = name
            self.repo.record_event(
                self.cid, "drain", "{} was drained below 1st level and died.".format(name),
                in_game_date=self._date())
            return res
        # Reduce hit points in proportion to the levels lost.
        old_hp = row["hp_max"] or 1
        new_hp = max(1, int(round(old_hp * new_total / old_total)))
        cur = min(row["hp_current"] if row["hp_current"] is not None else new_hp, new_hp)
        self.repo.conn.execute(
            "UPDATE character SET classes_json=?, hp_max=?, hp_current=? WHERE id=?",
            (json.dumps(res["classes"]), new_hp, cur, row["id"]))
        self.repo.conn.commit()
        res["name"] = name
        res["hp_max"] = new_hp
        for lv in res["levels_lost"]:
            self.repo.record_event(
                self.cid, "drain", "{} drained: {} {} -> {}.".format(
                    name, lv["class"], lv["from"], lv["to"]),
                in_game_date=self._date())
        return res

    def item_save(self, material: str, attack: str,
                  magic_bonus: int = 0) -> Dict[str, Any]:
        return cond_mod.item_save(self.dice, material, attack, int(magic_bonus))

    def _combatant_profile(self, row: Dict[str, Any],
                           size: Optional[str] = None) -> Dict[str, Any]:
        smods = ab_mod.strength_mods(row["str_score"] or 10, row["str_pct"] or 0)
        _, lvl = self._class_level(row)
        is_npc = bool(row["is_npc"]) if "is_npc" in row.keys() else False
        return {"ac": row["ac_descending"] if row["ac_descending"] is not None else 10,
                "dex": row["dex_score"] or 10, "str": row["str_score"] or 10,
                "str_damage": smods["damage"],
                "hd": lvl if is_npc else None,
                "size": (size or "medium"),
                "move": enc_mod.eq.RACE_BASE_MOVE.get(row["race"] or "Human", 120)}

    def grapple(self, attacker: str, defender: str, mode: str = "grapple",
                attacker_size: Optional[str] = None,
                defender_size: Optional[str] = None) -> Dict[str, Any]:
        _, err = self._require_turn(attacker)
        if err:
            return err
        a, d = self._find_char(attacker), self._find_char(defender)
        if not a or not d:
            return {"error": "attacker or defender not found"}
        res = cond_mod.unarmed_attack(
            self.dice, mode, self._combatant_profile(a, attacker_size),
            self._combatant_profile(d, defender_size))
        res["attacker"], res["defender"] = attacker, defender
        if res.get("real_damage"):
            self._apply_damage(dict(d), res["real_damage"])
            res["defender_hp"] = self._current_hp(d["id"])
        self.repo.record_event(
            self.cid, "grapple", "{} {}s {}: {}.".format(
                attacker, mode, defender,
                res.get("hold") or res.get("result")),
            in_game_date=self._date())
        snap = self._mark_acted(attacker)
        if snap:
            res["combat"] = snap
        return res

    # ---- death's door (OSRIC 1.6.6): 0 = down & bleeding, -10 = dead ----
    def _death_door_state(self, row: Dict[str, Any], new_hp: int):
        """Map an HP total to (hp, alive, status). Player characters are unconscious
        and 'dying' from 0 to -9, dead at -10. NPCs/monsters die at 0 or below."""
        is_pc = not bool(row["is_npc"]) if "is_npc" in row.keys() else True
        if not is_pc:
            if new_hp <= 0:
                return 0, 0, "dead"
            return new_hp, 1, (row["status"] if row["status"] not in (None, "dead") else "ok")
        if new_hp <= -10:
            return new_hp, 0, "dead"
        if new_hp <= 0:
            return new_hp, 1, "dying"           # unconscious, losing 1 hp/round
        return new_hp, 1, "ok"

    def _write_hp(self, row: Dict[str, Any], new_hp: int,
                  explicit_status: Optional[str] = None,
                  from_damage: bool = False):
        is_pc = not bool(row["is_npc"]) if "is_npc" in row.keys() else True
        prev = row["hp_current"] if row["hp_current"] is not None else row["hp_max"]
        # A fresh wound taken while already down (0 or below) is instantly fatal --
        # but only for actual damage, not bleeding or a manual set.
        if (from_damage and is_pc and prev is not None and prev <= 0
                and int(new_hp) < prev):
            hp, alive, status = int(new_hp), 0, "dead"
        else:
            hp, alive, status = self._death_door_state(row, int(new_hp))
        if explicit_status and status != "dead":
            status = explicit_status
        self.repo.conn.execute(
            "UPDATE character SET hp_current=?, alive=?, status=? WHERE id=?",
            (hp, alive, status, row["id"]))
        self.repo.conn.commit()
        return {"hp": hp, "alive": bool(alive), "status": status}

    def _apply_damage(self, row: Dict[str, Any], dmg: int) -> Dict[str, Any]:
        cur = (row["hp_current"] if row["hp_current"] is not None else row["hp_max"]) or 0
        return self._write_hp(row, cur - int(dmg), from_damage=int(dmg) > 0)

    def _current_hp(self, chid: int) -> int:
        r = self.repo.get_character(chid)
        return r["hp_current"] if r else 0

    # ---- initiative & the combat round --------------------------------
    def _combatant_spec(self, c: Dict[str, Any]) -> Dict[str, Any]:
        """Fill in a combatant's Dexterity (from their sheet) and weapon speed
        (from the catalog) so initiative can be rolled."""
        spec = {"name": c.get("name", "?"), "side": c.get("side", "party"),
                "action": (c.get("action") or "melee").lower(),
                "casting_time": int(c.get("casting_time", 0) or 0)}
        dex = c.get("dex")
        if dex is None:
            row = self._find_char(spec["name"])
            dex = (row["dex_score"] if row else 10) or 10
        spec["dex"] = int(dex)
        speed = c.get("weapon_speed")
        if speed is None and c.get("weapon"):
            w = equip_data.lookup(c["weapon"])
            speed = w.get("speed") if w else None
        spec["weapon_speed"] = int(speed) if speed is not None else 5
        return spec

    def _is_alive(self, name: str) -> bool:
        ch = self._find_char(name)
        if not ch:
            return True                          # unknown combatant: assume active
        if ch["alive"] == 0:
            return False
        return ch["hp_current"] is None or ch["hp_current"] > 0

    def _pending(self, cb: Dict[str, Any]) -> List[str]:
        """Living combatants who have not yet acted this round."""
        acted = {n.lower() for n in json.loads(cb["acted_json"] or "[]")}
        out = []
        for c in json.loads(cb["combatants_json"] or "[]"):
            nm = c.get("name", "?")
            if nm.lower() not in acted and self._is_alive(nm):
                out.append(nm)
        return out

    def _mark_acted(self, name: str) -> Optional[Dict[str, Any]]:
        """Record that `name` took their action this round. Returns the combat
        snapshot (round + who's still pending), or None if no active combat."""
        cb = self.repo.active_combat(self.cid)
        if not cb:
            return None
        acted = json.loads(cb["acted_json"] or "[]")
        if name not in acted:
            acted.append(name)
            self.repo.update_combat(cb["id"], acted_json=json.dumps(acted))
        cb = self.repo.active_combat(self.cid)
        pending = self._pending(dict(cb))
        return {"round": cb["round"], "pending": pending,
                "round_complete": not pending}

    def _require_turn(self, actor: str):
        """Gate a combat action. Returns (cb_row, None) if the action may proceed,
        or (None, error_dict) explaining why not -- so attacks can only happen
        inside a tracked combat, and the AI can't skip anyone's turn."""
        cb = self.repo.active_combat(self.cid)
        if not cb:
            return None, {"error": "No active combat. Call start_combat to roll "
                          "initiative first -- attacks are only resolved within a "
                          "tracked combat round."}
        roster = {c.get("name", "").lower() for c in
                  json.loads(cb["combatants_json"] or "[]")}
        if actor.lower() not in roster:
            return None, {"error": "{} is not in this combat. Add them via "
                          "start_combat, or end_combat first.".format(actor)}
        return cb, None

    def start_combat(self, combatants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Begin a tracked combat. combatants: [{name, side, action?, weapon?,
        dex?, casting_time?}]. Rolls the first round's initiative order."""
        specs = [self._combatant_spec(c) for c in (combatants or [])]
        if not specs:
            return {"error": "no combatants"}
        order = init_mod.roll_order(self.dice, specs)
        combat_id = self.repo.start_combat(
            self.cid, json.dumps(specs), json.dumps(order))
        self.repo.record_event(self.cid, "combat",
                               "Combat begins ({} combatants).".format(len(specs)),
                               in_game_date=self._date())
        return {"combat_id": combat_id, "round": 1, "order": order,
                "pending": [o["name"] for o in order if self._is_alive(o["name"])],
                "note": "Resolve every combatant's action (attack or advance_turn) "
                        "before next_round will advance."}

    def advance_turn(self, name: str, note: Optional[str] = None) -> Dict[str, Any]:
        """Mark a combatant's NON-attack action done this round (they moved, cast a
        utility spell, defended, fled...). Use this so the round can advance."""
        cb, err = self._require_turn(name)
        if err:
            return err
        snap = self._mark_acted(name)
        if note:
            self.repo.record_event(self.cid, "combat", "{}: {}".format(name, note),
                                   in_game_date=self._date())
        return {"acted": name, **snap}

    def _apply_bleeding(self) -> List[Dict[str, Any]]:
        """Each round, characters at death's door (status 'dying') lose 1 hp;
        at -10 they die. Stabilised characters don't bleed."""
        bled = []
        for r in self.repo.list_characters(self.cid):
            if r["status"] == "dying" and r["alive"] == 1:
                state = self._write_hp(dict(r), (r["hp_current"] or 0) - 1)
                bled.append({"name": r["name"], "hp": state["hp"],
                             "dead": state["status"] == "dead"})
                if state["status"] == "dead":
                    self.repo.record_event(
                        self.cid, "combat", "{} bled out and died.".format(r["name"]),
                        in_game_date=self._date())
        return bled

    def stabilize(self, name: str) -> Dict[str, Any]:
        """Bind a dying character's wounds: stops the 1-hp/round bleeding. They
        stay unconscious at their current HP until healed."""
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        if (row["hp_current"] or 0) > 0:
            return {"name": name, "note": "not at death's door", "status": row["status"]}
        self.repo.conn.execute(
            "UPDATE character SET status='stable', alive=1 WHERE id=?", (row["id"],))
        self.repo.conn.commit()
        self.repo.record_event(self.cid, "combat", "{} was stabilised.".format(name),
                               in_game_date=self._date())
        return {"name": name, "status": "stable", "hp": row["hp_current"]}

    def next_round(self, actions: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Advance to the next combat round, re-rolling initiative (OSRIC re-rolls
        each round). REFUSES while any living combatant still has to act -- so the
        foes can't be skipped. actions [{name, action, weapon, casting_time}]
        updates what people do next round (e.g. switching to a spell)."""
        cb = self.repo.active_combat(self.cid)
        if not cb:
            return {"error": "no active combat"}
        pending = self._pending(dict(cb))
        if pending:
            return {"error": "Round {} isn't over. These combatants haven't acted "
                    "yet: {}. Resolve each (attack or advance_turn) first.".format(
                        cb["round"], ", ".join(pending)),
                    "pending": pending, "round": cb["round"]}
        specs = json.loads(cb["combatants_json"])
        if actions:
            by_name = {s["name"].lower(): s for s in specs}
            for a in actions:
                s = by_name.get((a.get("name") or "").lower())
                if not s:
                    continue
                if a.get("action"):
                    s["action"] = a["action"].lower()
                if a.get("casting_time") is not None:
                    s["casting_time"] = int(a["casting_time"])
                if a.get("weapon"):
                    w = equip_data.lookup(a["weapon"])
                    if w and w.get("speed") is not None:
                        s["weapon_speed"] = int(w["speed"])
        bled = self._apply_bleeding()            # blood loss between rounds
        order = init_mod.roll_order(self.dice, specs)
        rnd = cb["round"] + 1
        self.repo.update_combat(cb["id"], round=rnd,
                                combatants_json=json.dumps(specs),
                                order_json=json.dumps(order), acted_json="[]")
        out = {"combat_id": cb["id"], "round": rnd, "order": order,
               "pending": [o["name"] for o in order if self._is_alive(o["name"])]}
        if bled:
            out["bleeding"] = bled
        return out

    def combat_status(self) -> Dict[str, Any]:
        cb = self.repo.active_combat(self.cid)
        if not cb:
            return {"active": False}
        return {"active": True, "round": cb["round"],
                "order": json.loads(cb["order_json"]),
                "acted": json.loads(cb["acted_json"] or "[]"),
                "pending": self._pending(dict(cb))}

    def end_combat(self) -> Dict[str, Any]:
        cb = self.repo.active_combat(self.cid)
        if not cb:
            return {"active": False}
        self.repo.end_combat(self.cid)
        self.repo.record_event(self.cid, "combat",
                               "Combat ends (after {} rounds).".format(cb["round"]),
                               in_game_date=self._date())
        return {"ended": True, "rounds": cb["round"]}

    # ---- the magic economy: learning, research, scribing, brewing -----
    def _caster(self, row: Dict[str, Any]):
        """Best spellcasting class for a character: (class, level, arcane?, ability)."""
        best = None
        for c in json.loads(row["classes_json"] or "[]"):
            cl = c.get("class")
            arcane = cl in mage_mod.ARCANE_CLASSES
            divine = cl in mage_mod.DIVINE_CLASSES
            if not (arcane or divine):
                continue
            lvl = int(c.get("level", 1))
            if best is None or lvl > best[1]:
                ability = row["int_score"] if arcane else row["wis_score"]
                best = (cl, lvl, arcane, ability or 10)
        return best

    def _caster_level_for_spell(self, row: Dict[str, Any], spec):
        """Caster level for a SPECIFIC spell: the character's level in the class
        that actually owns it. A Cleric/Magic-User casts a Magic-User spell at
        their Magic-User level, not their (possibly higher) Cleric level."""
        classes = json.loads(row["classes_json"] or "[]")
        owners = (spec or {}).get("classes") or []
        if owners:
            levels = [int(c.get("level", 1)) for c in classes
                      if c.get("class") in owners]
            if levels:
                return max(levels)
        cast = self._caster(row)
        if cast:
            return cast[1]
        return self._class_level(row)[1]

    def _spellbook_add(self, row: Dict[str, Any], spell: str) -> list:
        book = json.loads(row["spellbook_json"] or "[]")
        if spell not in book:
            book.append(spell)
        self.repo.conn.execute("UPDATE character SET spellbook_json=? WHERE id=?",
                               (json.dumps(book), row["id"]))
        return book

    def _charge(self, row: Dict[str, Any], amount: int) -> bool:
        have = row["gold"] or 0
        if amount > have:
            return False
        self.repo.conn.execute("UPDATE character SET gold=? WHERE id=?",
                               (have - amount, row["id"]))
        return True

    def learn_spell(self, name: str, spell: str, spell_level: int) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        caster = self._caster(dict(row))
        if not caster:
            return {"error": "{} is not a spellcaster".format(name)}
        cl, lvl, arcane, ability = caster
        res = mage_mod.learn_spell(self.dice, ability, int(spell_level),
                                   divine=not arcane)
        if not self._charge(dict(row), res["cost_gp"]):
            return {"error": "not enough gold for ink", "cost_gp": res["cost_gp"]}
        if res["understood"]:
            res["spellbook"] = self._spellbook_add(dict(row), spell)
        self.repo.conn.commit()
        res.update({"name": name, "spell": spell, "class": cl})
        self.repo.record_event(
            self.cid, "magic", "{} {} to learn {}.".format(
                name, "succeeded" if res["understood"] else "failed", spell),
            in_game_date=self._date())
        return res

    def research_spell(self, name: str, spell: str, spell_level: int,
                       increments: int = 0, has_facility: bool = True) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        caster = self._caster(dict(row))
        if not caster:
            return {"error": "{} is not a spellcaster".format(name)}
        cl, lvl, arcane, ability = caster
        res = mage_mod.research_spell(self.dice, ability, lvl, int(spell_level),
                                      int(increments), bool(has_facility))
        if not self._charge(dict(row), res["cost_gp"]):
            return {"error": "not enough gold for research", "cost_gp": res["cost_gp"]}
        if res["success"]:
            res["spellbook"] = self._spellbook_add(dict(row), spell)
        self.repo.conn.commit()
        res.update({"name": name, "spell": spell, "class": cl})
        self.repo.record_event(
            self.cid, "magic", "{} researched {}: {}.".format(
                name, spell, "success" if res["success"] else "no breakthrough"),
            in_game_date=self._date())
        return res

    def _require_crafter(self, row: Dict[str, Any]):
        caster = self._caster(row)
        if not caster:
            return None, "{} is not a spellcaster".format(row["name"])
        if caster[1] < mage_mod.CRAFT_LEVEL:
            return None, "{} must be level {}+ to craft magic".format(
                row["name"], mage_mod.CRAFT_LEVEL)
        return caster, None

    def scribe_scroll(self, name: str, spell: str, spell_level: int,
                      overworked: bool = False) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        caster, err = self._require_crafter(dict(row))
        if err:
            return {"error": err}
        res = mage_mod.scribe_scroll(self.dice, int(spell_level), bool(overworked))
        if not self._charge(dict(row), res["cost_gp"]):
            return {"error": "not enough gold", "cost_gp": res["cost_gp"]}
        if res["success"]:
            gear = json.loads(row["gear_json"] or "[]")
            gear.append({"item": "Scroll: {} (L{})".format(spell, spell_level),
                         "qty": 1, "weight": 0})
            self.repo.conn.execute("UPDATE character SET gear_json=? WHERE id=?",
                                   (json.dumps(gear), row["id"]))
        self.repo.conn.commit()
        res.update({"name": name, "spell": spell})
        self.repo.record_event(
            self.cid, "magic", "{} scribes a scroll of {}: {}.".format(
                name, spell, "done" if res["success"] else "failed"),
            in_game_date=self._date())
        return res

    def brew_potion(self, name: str, potion: str,
                    value_gp: int) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        caster, err = self._require_crafter(dict(row))
        if err:
            return {"error": err}
        res = mage_mod.brew_potion(self.dice, int(value_gp))
        if not self._charge(dict(row), res["cost_gp"]):
            return {"error": "not enough gold", "cost_gp": res["cost_gp"]}
        gear = json.loads(row["gear_json"] or "[]")
        gear.append({"item": "Potion: {}".format(potion), "qty": 1, "weight": 0.5})
        self.repo.conn.execute("UPDATE character SET gear_json=? WHERE id=?",
                               (json.dumps(gear), row["id"]))
        self.repo.conn.commit()
        res.update({"name": name, "potion": potion})
        self.repo.record_event(
            self.cid, "magic", "{} brews a potion of {}.".format(name, potion),
            in_game_date=self._date())
        return res

    def spells_available(self, name: str) -> Dict[str, Any]:
        """How many spells the character may memorise, per spell level."""
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        memorized = json.loads(row["memorized_json"] or "[]")
        avail, used = self._spell_slots(row)
        if not avail:
            return {"name": name, "caster": False,
                    "message": "{} is not a spellcaster.".format(name)}
        lvlmap = {c.get("class"): int(c.get("level", 1)) for c in self._classes_full(row)}
        by_class: Dict[str, Any] = {}
        flat = None
        for ccls, slots in avail.items():
            by_level = {i + 1: slots[i] for i in range(len(slots)) if slots[i] > 0}
            free = {i + 1: slots[i] - used[ccls].get(i + 1, 0)
                    for i in range(len(slots)) if slots[i] > 0}
            by_class[ccls] = {"level": lvlmap.get(ccls, 1),
                              "slots_by_spell_level": by_level, "free_by_spell_level": free}
            if flat is None:
                flat = {"class": ccls, "level": lvlmap.get(ccls, 1),
                        "slots_by_spell_level": by_level, "free_by_spell_level": free}
        out = {"name": name, "caster": True, "by_class": by_class,
               "memorized": memorized}
        out.update(flat)
        return out

    def list_spells(self, char_class: str, spell_level: int) -> Dict[str, Any]:
        names = [s.name for s in spell_catalog.for_class(char_class, spell_level)]
        return {"class": char_class, "spell_level": spell_level, "spells": names}

    def memorize_spell(self, name: str, spell: str,
                       spell_class: Optional[str] = None) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        memorized = json.loads(row["memorized_json"] or "[]")
        wis = row["wis_score"]
        # Route the spell to whichever of the character's classes owns it -- a
        # multi-class Cleric/Magic-User prepares from BOTH lists. spell_class
        # disambiguates a spell the classes share.
        owners = []
        for c in self._classes_full(row):
            ccls = c.get("class")
            if spell_class and ccls != spell_class:
                continue
            if spell_catalog.find(spell, ccls):
                owners.append((ccls, int(c.get("level", 1))))
        if not owners:
            sp_any = spell_catalog.find(spell)
            hint = " (it is a {} spell)".format(sp_any.char_class) if sp_any else ""
            return {"error": "{} cannot prepare {}{} -- not on the spell list of "
                    "{}.".format(name, spell, hint,
                    "/".join(c.get("class") for c in self._classes_full(row)))}
        avail, used = self._spell_slots(row)
        chosen = None
        for ccls, clvl in owners:
            sp = spell_catalog.find(spell, ccls)
            if (ccls in avail and sp.level - 1 < len(avail[ccls])
                    and used[ccls].get(sp.level, 0) < avail[ccls][sp.level - 1]):
                chosen = (ccls, clvl, sp); break
        if not chosen:
            sp = spell_catalog.find(spell, owners[0][0])
            return {"error": "no free level-{} slot for {} ({})".format(
                    sp.level, sp.name, "/".join(o[0] for o in owners))}
        ccls, clvl, sp = chosen
        new = list(memorized) + [sp.name]
        self.repo.conn.execute("UPDATE character SET memorized_json=? WHERE id=?",
                               (json.dumps(new), row["id"]))
        self.repo.conn.commit()
        return {"name": name, "memorized": new, "memorized_as": ccls}

    def _target_save_target(self, row: Dict[str, Any], cat: str) -> int:
        classes = json.loads(row["classes_json"] or "[]")
        norm = leveling_mod.normalize(classes)
        if norm:
            return leveling_mod.best_save_target(norm, cat)
        return saves_mod.save_target("Fighter", 1, cat)

    def _heal(self, row: Dict[str, Any], amount: int) -> int:
        cur = (row["hp_current"] if row["hp_current"] is not None else 0)
        new = min(row["hp_max"] or amount, cur + int(amount))
        self.repo.conn.execute(
            "UPDATE character SET hp_current=?, alive=1, status=? WHERE id=?",
            (new, "ok" if new > 0 else row["status"], row["id"]))
        self.repo.conn.commit()
        return new

    def cast_spell(self, name: str, spell: str,
                   targets: Optional[List[str]] = None,
                   caster_level: Optional[int] = None,
                   save_mod: int = 0) -> Dict[str, Any]:
        row = self._find_char(name)
        if not row:
            return {"error": "no character named {}".format(name)}
        memorized = json.loads(row["memorized_json"] or "[]")
        try:
            new = spellcasting.cast(memorized, spell)
        except ValueError as e:
            return {"error": str(e)}
        self.repo.conn.execute("UPDATE character SET memorized_json=? WHERE id=?",
                               (json.dumps(new), row["id"]))
        self.repo.conn.commit()
        out: Dict[str, Any] = {"name": name, "cast": spell, "memorized": new}

        # Resolve mechanical effect, if the spell has hard numbers.
        spec = spell_fx.lookup(spell)
        if caster_level:
            lvl = int(caster_level)
        else:
            lvl = self._caster_level_for_spell(dict(row), spec)
        if spec is None:
            out["resolved_by"] = "narration"
            try:
                out["rules"] = rules_lookup.rules(spell, limit=1)
            except Exception:
                out["rules"] = []
        elif spec["kind"] == "sleep":
            out["effect"] = "sleep"
            out["affected_by_hd"] = spell_fx.sleep_affected(self.dice)
            out["note"] = "No save. Apply 'asleep' to the affected creatures."
        elif spec["kind"] == "incapacitate":
            out["effect"] = "incapacitate"
            res = []
            for tn in (targets or []):
                tr = self._find_char(tn)
                if not tr:
                    continue
                tgt = self._target_save_target(dict(tr), spec.get("save_cat", "death"))
                roll = self.dice.d20() + int(save_mod)
                saved = roll >= tgt
                rounds = 0 if saved else self.dice.notation(spec["dice"]).total
                res.append({"target": tn, "save_roll": roll, "save_target": tgt,
                            "saved": saved, "rounds_incapacitated": rounds})
            out["targets"] = res
        elif spec["kind"] == "heal":
            tgt_name = (targets or [name])[0]
            tr = self._find_char(tgt_name)
            if not tr:
                return {**out, "error": "heal target {} not found".format(tgt_name)}
            roll = spell_fx.roll_amount(self.dice, spec, lvl)
            new_hp = self._heal(dict(tr), roll["amount"])
            out["effect"] = "heal"
            out["target"] = tgt_name
            out["healed"] = roll["amount"]
            out["detail"] = roll["detail"]
            out["target_hp"] = new_hp
        elif spec["kind"] == "damage":
            roll = spell_fx.roll_amount(self.dice, spec, lvl)
            amount = roll["amount"]
            cat = spec.get("save_cat", "spells")
            res = []
            for tn in (targets or []):
                tr = self._find_char(tn)
                if not tr:
                    continue
                applied = amount
                saved = None
                if spec.get("save", "none") != "none":
                    tgt = self._target_save_target(dict(tr), cat)
                    sroll = self.dice.d20() + int(save_mod)
                    saved = sroll >= tgt
                    if saved:
                        applied = amount // 2 if spec["save"] == "half" else 0
                self._apply_damage(dict(tr), applied)
                res.append({"target": tn, "damage": applied, "saved": saved,
                            "hp": self._current_hp(tr["id"])})
            out["effect"] = "damage"
            out["rolled"] = amount
            out["detail"] = roll["detail"]
            out["save"] = spec.get("save", "none")
            out["targets"] = res
            self.repo.record_event(
                self.cid, "spell", "{} casts {} ({} dmg) on {}.".format(
                    name, spec["name"], amount,
                    ", ".join(t["target"] for t in res) or "no one"),
                in_game_date=self._date())

        snap = self._mark_acted(name)            # casting is this caster's action
        if snap:
            out["combat"] = snap
        return out

    def _monster(self, name: str):
        m = bestiary.get(name)
        if not m:
            hits = bestiary.search(name)
            m = hits[0] if hits else None
        return m

    def get_monster(self, name: str) -> Dict[str, Any]:
        m = self._monster(name)
        if not m:
            return {"error": "no monster named {}".format(name)}
        return {"name": m.name, "hit_dice": m.hit_dice, "ac": m.ac_descending,
                "ac_ascending": m.ac_ascending, "attacks": m.attacks,
                "morale": m.morale, "size": m.size,
                "no_encountered": m.no_encountered, "xp": m.xp,
                "intelligence": m.intelligence, "alignment": m.alignment,
                "move": m.move, "attack_bonus": m.attack_bonus,
                "primary_damage": m.primary_damage()}

    def spawn_monster(self, name: str, label: Optional[str] = None,
                      count: int = 1) -> Dict[str, Any]:
        """Create count monsters as NPC combatants (HP rolled) so they can fight."""
        m = self._monster(name)
        if not m:
            return {"error": "no monster named {}".format(name)}
        count = max(1, min(int(count), 20))
        spawned = []
        for i in range(count):
            hp = bestiary.roll_hp(self.dice, m)
            base = label or m.name
            nm = base if count == 1 else "{} {}".format(base, i + 1)
            chid = self.repo.save_character(self.cid, {
                "name": nm, "race": m.name,
                "classes": [{"class": "Fighter", "level": m.hd_value, "xp": 0}],
                "alignment": m.alignment, "str": 10, "dex": 10, "con": 10,
                "int": 10, "wis": 10, "cha": 10,
                "hp_max": hp, "hp_current": hp,
                "ac_descending": m.ac_descending, "ac_ascending": m.ac_ascending,
                "damage_dice": m.primary_damage(),
                "notes": "Monster: {} (HD {}; {})".format(m.name, m.hit_dice, m.attacks),
            }, is_npc=True)
            spawned.append({"id": chid, "name": nm, "hp": hp, "ac": m.ac_descending})
        return {"monster": m.name, "attacks": m.attacks, "spawned": spawned}

    def generate_treasure(self, loot: str) -> Dict[str, Any]:
        """Roll treasure for one or more OSRIC loot classes (e.g. 'Hoard 3')."""
        classes = treasure_mod.loot_classes_in(loot) or [loot.strip()]
        t = treasure_mod.generate(self.dice, *classes)
        return {"loot_classes": classes, "coins": t.coins, "gems": t.gems,
                "jewellery": t.jewellery, "magic": t.magic,
                "total_value_gp": t.total_gp}

    def roll_magic_item(self, category: Optional[str] = None,
                        count: int = 1) -> Dict[str, Any]:
        """Roll random named magic item(s), optionally by category."""
        count = max(1, min(int(count), 12))
        items = []
        for _ in range(count):
            it = magic_mod.random_item(self.dice, category)
            if it:
                items.append({"name": it.name, "category": it.category})
        return {"items": items, "category": category or "any"}

    def _party_best(self, party, field: str, default: int = 10) -> int:
        best = default
        for n in (party or []):
            r = self._find_char(n)
            if r and (r[field] or 0) > best:
                best = r[field]
        return best

    def random_encounter(self, terrain: str,
                         party: Optional[List[str]] = None,
                         foe_surprises_on: int = 2,
                         context: Optional[str] = None,
                         region: Optional[str] = None,
                         subregion: Optional[str] = None) -> Dict[str, Any]:
        """Roll a wandering monster for a terrain or dungeon depth and report its
        number appearing and stats -- plus the surprise roll and the monster's
        reaction, so the encounter arrives fully formed.

        A monster's no_encountered is its LAIR / full social-grouping ceiling.
        By default we roll an encounter CONTEXT (scouting patrol, hunting party,
        raiding warband, large band, full muster) and scale that ceiling by it,
        so you meet a patrol far more often than a whole tribe on the move. Pass
        context='lair' (or a named context) to force the kind of meeting.

        Pass region to roll a rich Known World d100 table instead of the bare
        terrain list -- one per realm: 'frostmark', 'karth', 'vaultholme',
        'khalassar', 'yselmark', 'aurenne', 'valmoria', 'sundering-scar',
        'pallid-cities', 'bonelands', 'march-of-coin', 'halvedd', 'gloamhold',
        'lumenar', 'scarlet-isles', 'tidereach', 'sahl', 'qoph', 'ymmu',
        'eldwood', plus the dungeon 'leaning-tower'. The home march 'halvedd'
        takes a subregion ('farmland'/'road'/'ashmarch'/'tumblewood'/
        'barrowdowns'); 'leaning-tower' takes 'upper'/'lower'. A 'Use Standard'
        result falls back to the region's terrain list. (Tables in
        engine/data/encounters.py; combat rows spawn real bestiary stats,
        descriptive rows are set-pieces you play.)"""
        region_name = None
        subregion_used = None
        from_standard_table = False
        if region:
            rname, from_standard_table, subregion_used = \
                encounters_mod.roll_region(self.dice, region, subregion)
            region_name = region
            if rname is None:
                fb = encounters_mod.region_fallback(region) or terrain
                name = encounters_mod.roll(self.dice, fb)
            else:
                name = rname
        else:
            name = encounters_mod.roll(self.dice, terrain)
        if not name:
            return {"error": "unknown terrain '{}'".format(terrain),
                    "terrains": encounters_mod.terrains(),
                    "regions": encounters_mod.regions()}
        m = self._monster(name)
        if context:
            frac = encounters_mod.context_fraction(context)
            if frac is not None:
                ctx_name, ctx_frac = context, frac
            else:
                ctx_name, ctx_frac = encounters_mod.roll_context(self.dice)
        else:
            ctx_name, ctx_frac = encounters_mod.roll_context(self.dice)
        number = 1
        lair_strength = 1
        if m and m.no_encountered:
            tok = m.no_encountered.split()[0]
            try:
                lair_strength = max(1, self.dice.notation(tok).total)
            except Exception:
                lair_strength = 1
            number = max(1, int(round(lair_strength * ctx_frac)))
        surprise = explore_mod.surprise(
            self.dice, self._party_best(party, "dex_score"), 10,
            int(foe_surprises_on))
        reaction = hench_mod.reaction_roll(
            self.dice, loyalty_data.reaction_modifier(
                self._party_best(party, "cha_score")))
        return {"terrain": terrain, "monster": name,
                "in_bestiary": m is not None, "number_appearing": number,
                "context": ctx_name, "lair_strength": lair_strength,
                "region": region_name, "subregion": subregion_used,
                "from_standard_table": from_standard_table,
                "surprise": surprise, "reaction": reaction,
                "stats": (self.get_monster(m.name) if m else None)}

    def generate_weather(self, season: str = "spring") -> Dict[str, Any]:
        return weather_mod.generate(self.dice, season)

    def _party_move(self, party) -> Optional[int]:
        """The party travels at its slowest member's encumbrance-adjusted move."""
        rates = []
        for n in (party or []):
            r = self._find_char(n)
            if not r:
                continue
            gear = json.loads(r["gear_json"] or "[]")
            a = enc_mod.assess(gear, r["gold"] or 0, r["str_score"] or 10,
                               r["str_pct"] or 0, r["race"] or "Human")
            rates.append(a["movement_rate"])
        return min(rates) if rates else None

    def journey(self, terrain: str, days: int = 1, season: str = "spring",
                base_move: int = 120, has_guide: bool = False,
                party: Optional[List[str]] = None) -> Dict[str, Any]:
        """Travel overland: each day rolls weather, distance, getting-lost, and a
        1-in-6 wandering-monster check. Pass party (names) and the party moves at
        its slowest, most-encumbered member's rate; otherwise base_move is used."""
        days = max(1, min(int(days), 30))
        party_move = self._party_move(party)
        move = party_move if party_move is not None else int(base_move)
        total, log = 0, []
        for d in range(1, days + 1):
            w = weather_mod.generate(self.dice, season)
            leg = travel_mod.travel_day(self.dice, int(move), terrain,
                                        bool(has_guide))
            total += leg["miles"]
            enc = encounters_mod.roll(self.dice, terrain) \
                if self.dice.d6() == 1 else None
            log.append({"day": d, "miles": leg["miles"], "lost": leg["lost"],
                        "weather": "{}, {}F, {}, {}".format(
                            w["sky"], w["temperature_f"], w["precipitation"],
                            w["wind"]),
                        "encounter": enc})
        return {"terrain": terrain, "days": days, "total_miles": total,
                "movement_rate": move,
                "movement_from": "party encumbrance" if party_move is not None
                                 else "base_move", "log": log}

    def travel_route(self, legs: List[Dict[str, Any]], miles_per_hex: int = 6,
                     season: str = "spring", base_move: int = 120,
                     party: Optional[List[str]] = None,
                     advance: bool = True) -> Dict[str, Any]:
        """Resolve an overland route read off the shared map -- the engine does
        ALL the distance/time math. Each leg is {"terrain": <plains|road|forest|
        hills|mountains|swamp|desert|...>, "hexes": N} (or "miles": M instead of
        hexes). The digital Darlene hex overlay is 6 miles/hex. Uses encumbered pace,
        sums the days, advances the AS calendar, and returns a per-leg breakdown
        plus the arrival date. Pass party=[names] for true encumbered pace."""
        import math
        party_move = self._party_move(party)
        move = party_move if party_move is not None else int(base_move)
        out_legs, total_miles, total_days = [], 0, 0
        for leg in (legs or []):
            terrain = (leg.get("terrain") or "plains")
            if leg.get("miles") is not None:
                miles = int(leg["miles"])
            else:
                miles = int(leg.get("hexes", 0)) * int(miles_per_hex)
            rate = travel_mod.miles_per_day(int(move), terrain)
            days = max(1, math.ceil(miles / rate)) if miles > 0 else 0
            total_miles += miles
            total_days += days
            out_legs.append({"terrain": terrain, "hexes": leg.get("hexes"),
                             "miles": miles, "miles_per_day": rate, "days": days})
        new_date = (self._advance_calendar(total_days)
                    if (advance and total_days) else self._date())
        return {"legs": out_legs, "total_miles": total_miles,
                "total_days": total_days, "miles_per_hex": int(miles_per_hex),
                "movement_rate": move,
                "movement_from": "party encumbrance" if party_move is not None
                                 else "base_move",
                "arrival_date": new_date}

    # ---- trade & vessels ----------------------------------------------
    @staticmethod
    def _econs(s) -> List[str]:
        if isinstance(s, list):
            return [e.strip() for e in s if str(e).strip()]
        return [e.strip() for e in (s or "").split(",") if e.strip()]

    def _vessel_capacity(self, row) -> Optional[float]:
        vj = json.loads(row["vessel_json"] or "null") if "vessel_json" in row.keys() else None
        if not vj:
            return None
        v = vessels_mod.fit(vj.get("type"), vj.get("addons"))
        return v.capacity_tons if v else None

    def list_vessels(self) -> Dict[str, Any]:
        out = []
        for name, v in vessels_mod.VESSELS.items():
            out.append({"name": name, "category": v.category,
                        "capacity_tons": v.capacity_tons, "cost_gp": v.cost_gp,
                        "speed_factor": v.speed_factor, "terrains": list(v.terrains),
                        "addon_slots": v.addon_slots})
        return {"vessels": out, "addons": list(vessels_mod.ADDONS.keys())}

    def set_vessel(self, trader: str, vessel_type: str,
                   addons: Optional[List[str]] = None) -> Dict[str, Any]:
        row = self._find_char(trader)
        if not row:
            return {"error": "no character named {}".format(trader)}
        v = vessels_mod.fit(vessel_type, addons or [])
        if not v:
            return {"error": "unknown vessel '{}'".format(vessel_type)}
        self.repo.conn.execute(
            "UPDATE character SET vessel_json=? WHERE id=?",
            (json.dumps({"type": v.vtype.name,
                         "addons": [a.name for a in v.addons]}), row["id"]))
        self.repo.conn.commit()
        return {"trader": trader, "vessel": v.vtype.name,
                "capacity_tons": v.capacity_tons, "speed_factor": v.speed_factor,
                "terrains": list(v.vtype.terrains)}

    @staticmethod
    def _derive_economies(kind, terrain) -> str:
        k = (kind or "").lower(); t = (terrain or "").lower(); tags = []
        coastal = any(w in t for w in ("water","coast","sea","ocean","lake","river","marsh"))
        if coastal: tags.append("Coastal")
        if coastal and k in ("city","town","port"): tags.append("Port")
        if any(w in t for w in ("forest","wood","jungle")): tags.append("Forest")
        if any(w in t for w in ("hill","mountain","badland")): tags.append("Mining")
        if any(w in t for w in ("plain","grass","field","farm","steppe","down")): tags.append("Agricultural")
        if k == "city": tags += ["Craft", "Rich"]
        elif k == "town": tags.append("Agricultural")
        elif k == "village": tags += ["Agricultural", "Frontier"]
        elif k == "dungeon": tags.append("Poor")
        seen = []
        for x in tags:
            if x not in seen: seen.append(x)
        return ", ".join(seen) or "Agricultural"

    def _current_economies(self):
        locs = [dict(r) for r in self.repo.list_locations(self.cid)]
        party = next((l for l in locs if (l.get("kind") or "") == "party"), None)
        if not party or party.get("hex_col") is None:
            return None, None
        here = [l for l in locs if (l.get("kind") or "") != "party"
                and l.get("hex_col") == party.get("hex_col")
                and l.get("hex_row") == party.get("hex_row")]
        if not here:
            return None, None
        loc = here[0]
        econ = loc.get("economies") or self._derive_economies(loc.get("kind"), loc.get("terrain"))
        return loc.get("name"), econ

    def _resolve_economies(self, economies):
        if economies:
            return economies, None
        place, econ = self._current_economies()
        return econ, place

    def market_goods(self, economies: Optional[str] = None,
                     trader: Optional[str] = None) -> Dict[str, Any]:
        economies, _place = self._resolve_economies(economies)
        if not economies:
            return {"error": "No economy known for the party location. Pass economies, or set_party_position onto a mapped settlement (add_location auto-derives an economy from kind/terrain)."}
        econs = self._econs(economies)
        market = trade_mod.available_goods(self.dice, econs)
        cha = 10
        if trader:
            row = self._find_char(trader)
            if row:
                cha = row["cha_score"] or 10
        for m in market:
            q = trade_mod.purchase_price(self.dice, m["good"], econs, cha)
            if q:
                m["buy_price_per_ton"] = q.price_per_ton
        out = {"economies": econs, "market": market}
        if _place:
            out["at"] = _place
        return out

    def buy_goods(self, trader: str, good: str, tons: int,
                  economies: Optional[str] = None) -> Dict[str, Any]:
        row = self._find_char(trader)
        if not row:
            return {"error": "no character named {}".format(trader)}
        if good not in trade_mod.GOODS:
            return {"error": "no trade good '{}'".format(good)}
        economies, _place = self._resolve_economies(economies)
        if not economies:
            return {"error": "No economy known for the party location. Pass economies, or set_party_position onto a mapped settlement (add_location auto-derives an economy from kind/terrain)."}
        econs = self._econs(economies)
        cha = row["cha_score"] or 10
        q = trade_mod.purchase_price(self.dice, good, econs, cha)
        cost = q.price_per_ton * int(tons)
        if cost > (row["gold"] or 0):
            return {"error": "can't afford", "cost": cost, "gold": row["gold"]}
        cargo = json.loads(row["cargo_json"] or "[]") if "cargo_json" in row.keys() else []
        used = sum(c["tons"] for c in cargo)
        cap = self._vessel_capacity(row)
        if cap is not None and used + tons > cap:
            return {"error": "exceeds vessel capacity", "capacity_tons": cap,
                    "in_use": used, "adding": tons}
        cargo.append({"good": good, "tons": int(tons), "buy_price": q.price_per_ton})
        self.repo.conn.execute(
            "UPDATE character SET gold=?, cargo_json=? WHERE id=?",
            ((row["gold"] or 0) - cost, json.dumps(cargo), row["id"]))
        self.repo.conn.commit()
        return {"trader": trader, "bought": good, "tons": int(tons),
                "price_per_ton": q.price_per_ton, "cost": cost,
                "gold": (row["gold"] or 0) - cost, "cargo_tons": used + tons}

    def sell_goods(self, trader: str, good: str, tons: int,
                   economies: Optional[str] = None) -> Dict[str, Any]:
        row = self._find_char(trader)
        if not row:
            return {"error": "no character named {}".format(trader)}
        economies, _place = self._resolve_economies(economies)
        if not economies:
            return {"error": "No economy known for the party location. Pass economies, or set_party_position onto a mapped settlement (add_location auto-derives an economy from kind/terrain)."}
        econs = self._econs(economies)
        cargo = json.loads(row["cargo_json"] or "[]") if "cargo_json" in row.keys() else []
        have = sum(c["tons"] for c in cargo if c["good"].lower() == good.lower())
        if tons > have:
            return {"error": "not enough cargo", "have_tons": have, "good": good}
        q = trade_mod.sale_price(self.dice, good, econs, row["cha_score"] or 10)
        if not q:
            return {"error": "no trade good '{}'".format(good)}
        revenue = q.price_per_ton * int(tons)
        # remove tons (and track cost basis for profit)
        remaining, basis = int(tons), 0
        for c in list(cargo):
            if remaining <= 0:
                break
            if c["good"].lower() == good.lower():
                take = min(remaining, c["tons"])
                basis += take * c.get("buy_price", 0)
                c["tons"] -= take
                remaining -= take
                if c["tons"] <= 0:
                    cargo.remove(c)
        self.repo.conn.execute(
            "UPDATE character SET gold=?, cargo_json=? WHERE id=?",
            ((row["gold"] or 0) + revenue, json.dumps(cargo), row["id"]))
        self.repo.conn.commit()
        return {"trader": trader, "sold": good, "tons": int(tons),
                "price_per_ton": q.price_per_ton, "revenue": revenue,
                "profit": revenue - basis, "gold": (row["gold"] or 0) + revenue}

    def get_cargo(self, trader: str) -> Dict[str, Any]:
        row = self._find_char(trader)
        if not row:
            return {"error": "no character named {}".format(trader)}
        cargo = json.loads(row["cargo_json"] or "[]") if "cargo_json" in row.keys() else []
        cap = self._vessel_capacity(row)
        return {"trader": trader, "cargo": cargo,
                "total_tons": sum(c["tons"] for c in cargo),
                "capacity_tons": cap, "gold": row["gold"]}

    # ---- the realm: dominions, strongholds, war -----------------------
    def _dom_from_row(self, row):
        fiefs = [domain_mod.Fief(**f) for f in json.loads(row["fiefs_json"] or "[]")]
        troops = [domain_mod.Troop(**t) for t in json.loads(row["troops_json"] or "[]")]
        return domain_mod.Dominion(name=row["name"], fiefs=fiefs,
                                   confidence=row["confidence"],
                                   tax_rate_gp=row["tax_rate_gp"],
                                   has_liege=bool(row["has_liege"]), troops=troops)

    def list_titles(self) -> Dict[str, Any]:
        return {"titles": [{"rank": t.rank, "name": t.name,
                            "dominions": t.dominions,
                            "entertain_gp_day": t.entertain_cost_day}
                           for t in domain_mod.TITLES]}

    def build_stronghold(self, elements: Dict[str, int],
                         region: str = "normal") -> Dict[str, Any]:
        return domain_mod.build_stronghold(elements or {}, region)

    def found_dominion(self, ruler: str, name: str, terrain: str,
                       civ_level: str = "wilderness", title: Optional[str] = None,
                       has_liege: bool = True) -> Dict[str, Any]:
        rc = self._find_char(ruler)
        ability_total = sum(rc[a] or 10 for a in ("str_score", "dex_score",
            "con_score", "int_score", "wis_score", "cha_score")) if rc else 60
        conf = domain_mod.initial_confidence(self.dice, ability_total)
        fief = domain_mod.found_fief(self.dice, terrain, civ_level)
        dom_id = self.repo.create_dominion(self.cid, name, ruler=ruler, title=title,
                                           confidence=conf, fiefs=[fief.__dict__])
        self.repo.update_dominion(dom_id, has_liege=1 if has_liege else 0)
        return {"dominion": name, "ruler": ruler, "title": title,
                "confidence": conf, "confidence_level": domain_mod.confidence_level(conf),
                "fief": fief.__dict__,
                "families": fief.families, "resources": fief.resources}

    def list_dominions(self) -> Dict[str, Any]:
        # Dedupe by name (newest wins) so a legacy duplicate row never shows twice.
        by_name = {}
        for r in self.repo.list_dominions(self.cid):   # ascending id; newest overwrites
            d = self._dom_from_row(r)
            by_name[r["name"].lower()] = {
                "name": r["name"], "ruler": r["ruler"], "title": r["title"],
                "families": d.families, "confidence": r["confidence"],
                "confidence_level": domain_mod.confidence_level(r["confidence"])}
        return {"dominions": list(by_name.values())}

    def set_dominion_tax(self, dominion: str, rate_gp: float) -> Dict[str, Any]:
        row = self.repo.get_dominion(self.cid, dominion)
        if not row:
            return {"error": "no dominion named {}".format(dominion)}
        d = self._dom_from_row(row)
        shift = domain_mod.set_tax_rate(d, float(rate_gp))
        self.repo.update_dominion(row["id"], tax_rate_gp=d.tax_rate_gp,
                                  confidence=d.confidence)
        return {"dominion": dominion, "tax_rate_gp": d.tax_rate_gp,
                "confidence_shift": shift, "confidence": d.confidence,
                "confidence_level": domain_mod.confidence_level(d.confidence)}

    def domain_turn(self, dominion: str, festivals: int = 0,
                    extra_expenses: int = 0) -> Dict[str, Any]:
        row = self.repo.get_dominion(self.cid, dominion)
        if not row:
            return {"error": "no dominion named {}".format(dominion)}
        d = self._dom_from_row(row)
        rep = domain_mod.monthly_turn(self.dice, d, festivals, extra_expenses)
        self.repo.update_dominion(
            row["id"], confidence=d.confidence,
            fiefs_json=json.dumps([f.__dict__ for f in d.fiefs]))
        # Bank the month's net cash into the ruler's purse.
        if row["ruler"]:
            rc = self._find_char(row["ruler"])
            if rc:
                self.repo.conn.execute(
                    "UPDATE character SET gold=? WHERE id=?",
                    (max(0, (rc["gold"] or 0) + rep["net_cash"]), rc["id"]))
                self.repo.conn.commit()
        rep["banked_to"] = row["ruler"]
        return rep

    def dominion_events(self, dominion: str,
                        count: Optional[int] = None) -> Dict[str, Any]:
        """Roll a dominion's yearly events from the premade deck and apply their
        Confidence and population effects; income modifiers are reported for the
        next domain turn."""
        row = self.repo.get_dominion(self.cid, dominion)
        if not row:
            return {"error": "no dominion named {}".format(dominion)}
        res = dom_events_mod.roll_yearly(self.dice, count)
        fiefs = json.loads(row["fiefs_json"] or "[]")
        conf = row["confidence"]
        for ev in res["events"]:
            conf += ev["confidence"]
            if ev["population_pct"] and fiefs:
                for f in fiefs:
                    f["families"] = max(0, round(f.get("families", 0)
                                                 * (1 + ev["population_pct"] / 100.0)))
            self.repo.record_event(
                self.cid, "realm", "{}: {} ({}).".format(
                    dominion, ev["event"], ev["category_label"]),
                detail=ev, in_game_date=self._date())
        conf = max(0, conf)
        self.repo.update_dominion(row["id"], confidence=conf,
                                  fiefs_json=json.dumps(fiefs))
        return {"dominion": dominion, "count": res["count"],
                "events": res["events"],
                "confidence_before": row["confidence"], "confidence_after": conf,
                "confidence_level": domain_mod.confidence_level(conf),
                "families_after": sum(f.get("families", 0) for f in fiefs),
                "income_modifiers": [{"event": e["event"], "income_pct": e["income_pct"]}
                                     for e in res["events"] if e["income_pct"]]}

    def _force(self, f: Dict[str, Any], default_name: str) -> "war_mod.Force":
        return war_mod.Force(
            name=f.get("name", default_name), troops=int(f.get("troops", 0)),
            troop_hd=float(f.get("hit_dice", 1)),
            troop_class=f.get("troop_class", "average"),
            leader_level=int(f.get("leader_level", 0)),
            leader_cha=int(f.get("leader_cha", 10)),
            mounted=bool(f.get("mounted")), missile=bool(f.get("missile")),
            spellcasters=int(f.get("spellcasters", 0)),
            fortified=bool(f.get("fortified")))

    def resolve_battle(self, attacker: Dict[str, Any], defender: Dict[str, Any],
                       siege: bool = False, attacker_terrain: int = 0,
                       defender_terrain: int = 0) -> Dict[str, Any]:
        a = self._force(attacker, "Attacker")
        d = self._force(defender, "Defender")
        if siege:
            result = war_mod.besiege(self.dice, a, d, attacker_terrain or -10)
        else:
            result = war_mod.resolve_battle(self.dice, a, d, attacker_terrain,
                                            defender_terrain)
        self.repo.record_event(
            self.cid, "battle",
            "{} defeated {}{}.".format(result["winner"], result["loser"],
                                       " (siege)" if siege else ""),
            detail=result, in_game_date=self._date())
        return result

    def _warship(self, s: Dict[str, Any], default_name: str) -> "naval_mod.Warship":
        common = dict(crew=int(s.get("crew", 10)),
                      crew_hd=float(s.get("crew_hd", 1)),
                      crew_class=s.get("crew_class", "average"),
                      ram=bool(s.get("ram")), artillery=int(s.get("artillery", 0)),
                      leader_level=int(s.get("leader_level", 0)),
                      leader_cha=int(s.get("leader_cha", 10)))
        if s.get("vessel_type"):
            crew = common.pop("crew")
            return naval_mod.from_vessel(s.get("name", default_name),
                                         s["vessel_type"], crew, **common)
        return naval_mod.Warship(name=s.get("name", default_name),
                                 tonnage=float(s.get("tonnage", 20)), **common)

    def naval_battle(self, ship_a: Dict[str, Any], ship_b: Dict[str, Any],
                     ram_a: bool = True, ram_b: bool = True) -> Dict[str, Any]:
        a = self._warship(ship_a, "Ship A")
        b = self._warship(ship_b, "Ship B")
        res = naval_mod.naval_battle(self.dice, a, b, bool(ram_a), bool(ram_b))
        self.repo.record_event(
            self.cid, "naval",
            "{} defeated {} at sea ({}).".format(
                res["winner"], res["loser"], res["loser_fate"]),
            detail=res, in_game_date=self._date())
        return res

    def record_event(self, summary: str, kind: str = "note") -> Dict[str, Any]:
        eid = self.repo.record_event(self.cid, kind, summary,
                                     in_game_date=self._date())
        return {"event_id": eid, "summary": summary}

    def recent_events(self, limit: int = 12) -> Dict[str, Any]:
        evs = [{"date": e["in_game_date"], "kind": e["kind"], "summary": e["summary"]}
               for e in self.repo.recent_events(self.cid, limit)]
        return {"events": list(reversed(evs))}

    # ---- story canon (locked arc / boss / theme truths) ---------------
    # A campaign bible the referee MUST honour: defined bosses, themes, win
    # conditions, and clocks, plus sealed DM-only secrets revealed through
    # play. Stored as a JSON document beside the campaign DB so it survives
    # compaction and is authoritative -- narration must never contradict it.
    def _canon_path(self) -> str:
        import os
        row = self.repo.conn.execute("PRAGMA database_list").fetchone()
        dbfile = (row["file"] if row and row["file"] else "") or ""
        base = os.path.dirname(dbfile) if dbfile else os.getcwd()
        return os.path.join(base or ".", "canon.json")

    def _canon_load(self) -> Dict[str, Any]:
        import json, os
        p = self._canon_path()
        if not os.path.exists(p):
            return {}
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _canon_save(self, data: Dict[str, Any]) -> None:
        import json
        with open(self._canon_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def define_canon(self, slug: str, title: Optional[str] = None,
                     kind: str = "arc", theme: Optional[str] = None,
                     boss: Optional[str] = None, public: Optional[str] = None,
                     secret: Optional[str] = None,
                     win_condition: Optional[str] = None,
                     clock: Optional[str] = None, status: str = "active",
                     notes: Optional[str] = None) -> Dict[str, Any]:
        """Lock a canonical story truth (an arc and its defined boss, theme,
        weakness/win_condition, and clock). Authoritative: narration must not
        contradict it. 'secret' holds sealed DM truths revealed only through
        play. Upserts by slug; only fields you pass are changed."""
        import time
        data = self._canon_load()
        camp = data.setdefault(str(self.cid), {})
        entry = camp.get(slug) or {"slug": slug,
                                   "created": time.strftime("%Y-%m-%d")}
        for k, v in (("title", title), ("kind", kind), ("theme", theme),
                     ("boss", boss), ("public", public), ("secret", secret),
                     ("win_condition", win_condition), ("clock", clock),
                     ("status", status), ("notes", notes)):
            if v is not None:
                entry[k] = v
        entry["updated"] = time.strftime("%Y-%m-%d")
        camp[slug] = entry
        self._canon_save(data)
        self.repo.record_event(self.cid, "canon",
                               "CANON locked: {} ({}).".format(title or slug, slug),
                               in_game_date=self._date())
        return {"saved": slug,
                "canon": {k: v for k, v in entry.items() if k != "secret"},
                "has_secret": bool(entry.get("secret"))}

    def get_canon(self, slug: str, reveal_secret: bool = False) -> Dict[str, Any]:
        """Read a locked canon entry by slug. Sealed 'secret' DM truths are
        hidden unless reveal_secret=True."""
        camp = self._canon_load().get(str(self.cid), {})
        entry = camp.get(slug)
        if not entry:
            return {"error": "no canon entry '{}'".format(slug)}
        if reveal_secret:
            return {"canon": entry}
        return {"canon": {k: v for k, v in entry.items() if k != "secret"},
                "has_secret": bool(entry.get("secret"))}

    def list_canon(self) -> Dict[str, Any]:
        """List all locked story-canon entries (boss, theme, status)."""
        camp = self._canon_load().get(str(self.cid), {})
        return {"canon": [
            {"slug": e.get("slug"), "title": e.get("title"),
             "kind": e.get("kind"), "boss": e.get("boss"),
             "theme": e.get("theme"), "status": e.get("status")}
            for e in camp.values()]}

    # ---- ventures (standing enterprises that pay over time) -----------
    # A lightweight business-income layer: each venture carries a monthly
    # yield and upkeep, and collect_ventures pays the accrued NET over the
    # elapsed months. Borrows the shape of Dark Dungeons dominion income +
    # Cepheus business overhead. Stored as JSON beside the DB (compaction-proof).
    def _ventures_path(self) -> str:
        import os
        row = self.repo.conn.execute("PRAGMA database_list").fetchone()
        dbfile = (row["file"] if row and row["file"] else "") or ""
        base = os.path.dirname(dbfile) if dbfile else os.getcwd()
        return os.path.join(base or ".", "ventures.json")

    def _ventures_load(self) -> Dict[str, Any]:
        import json, os
        p = self._ventures_path()
        if not os.path.exists(p):
            return {}
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _ventures_save(self, data: Dict[str, Any]) -> None:
        import json
        with open(self._ventures_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_venture(self, slug: str, name: Optional[str] = None,
                    kind: str = "enterprise", location: Optional[str] = None,
                    yield_gp: Optional[float] = None,
                    upkeep_gp: Optional[float] = None, status: str = "active",
                    notes: Optional[str] = None) -> Dict[str, Any]:
        """Register/update a standing enterprise that pays monthly. yield_gp and
        upkeep_gp are PER MONTH; net = yield - upkeep. Upserts by slug; only the
        fields you pass are changed."""
        import time
        data = self._ventures_load()
        camp = data.setdefault(str(self.cid), {})
        v = camp.get(slug) or {"slug": slug, "created": time.strftime("%Y-%m-%d")}
        for k, val in (("name", name), ("kind", kind), ("location", location),
                       ("yield_gp", yield_gp), ("upkeep_gp", upkeep_gp),
                       ("status", status), ("notes", notes)):
            if val is not None:
                v[k] = val
        v["updated"] = time.strftime("%Y-%m-%d")
        camp[slug] = v
        self._ventures_save(data)
        net = float(v.get("yield_gp", 0) or 0) - float(v.get("upkeep_gp", 0) or 0)
        return {"saved": slug, "venture": v, "net_per_month": round(net, 2)}

    def list_ventures(self) -> Dict[str, Any]:
        """List standing ventures with monthly yield, upkeep, and net."""
        camp = self._ventures_load().get(str(self.cid), {})
        out, total = [], 0.0
        for v in camp.values():
            y = float(v.get("yield_gp", 0) or 0)
            u = float(v.get("upkeep_gp", 0) or 0)
            net = y - u
            if v.get("status", "active") == "active":
                total += net
            out.append({"slug": v.get("slug"), "name": v.get("name"),
                        "location": v.get("location"), "yield_gp": y,
                        "upkeep_gp": u, "net_per_month": round(net, 2),
                        "status": v.get("status", "active")})
        return {"ventures": out, "net_per_month_total": round(total, 2)}

    def collect_ventures(self, months: float, deposit_to: str) -> Dict[str, Any]:
        """Pay out the accrued NET income (yield - upkeep) of all ACTIVE ventures
        over `months` months, crediting the character `deposit_to`."""
        row = self._find_char(deposit_to)
        if not row:
            return {"error": "no character named {}".format(deposit_to)}
        camp = self._ventures_load().get(str(self.cid), {})
        lines, total = [], 0.0
        for v in camp.values():
            if v.get("status", "active") != "active":
                continue
            net = (float(v.get("yield_gp", 0) or 0)
                   - float(v.get("upkeep_gp", 0) or 0)) * float(months)
            total += net
            lines.append({"slug": v.get("slug"), "name": v.get("name"),
                          "gp": round(net, 2)})
        total = int(round(total))
        old_gold = row["gold"] or 0
        new_gold = old_gold + total
        self.repo.conn.execute("UPDATE character SET gold=? WHERE id=?",
                               (new_gold, row["id"]))
        self.repo.conn.commit()
        self.repo.record_event(
            self.cid, "venture",
            "Collected {} months of venture income: {} gp net to {} (gold {} -> {}).".format(
                months, total, deposit_to, old_gold, new_gold),
            in_game_date=self._date())
        return {"months": months, "deposited_to": deposit_to,
                "net_collected_gp": total, "gold": new_gold, "breakdown": lines}

    # ---- the Flanaess hex map -----------------------------------------
    def add_location(self, name: str, kind: str = "landmark",
                     terrain: Optional[str] = None, col: Optional[int] = None,
                     row: Optional[int] = None, notes: str = "",
                     economies: Optional[str] = None) -> Dict[str, Any]:
        econ = economies or self._derive_economies(kind, terrain)
        lid = self.repo.add_location(self.cid, name, kind=kind, terrain=terrain,
                                     hex_col=col, hex_row=row, notes=notes,
                                     economies=econ)
        self.repo.record_event(
            self.cid, "map", "Mapped {} ({}) at hex {},{}.".format(
                name, kind, col, row), in_game_date=self._date())
        return {"location_id": lid, "name": name, "kind": kind,
                "terrain": terrain, "col": col, "row": row, "economies": econ}

    def list_locations(self) -> Dict[str, Any]:
        out, party = [], None
        for r in self.repo.list_locations(self.cid):
            d = {"name": r["name"], "kind": r["kind"], "terrain": r["terrain"],
                 "col": r["hex_col"], "row": r["hex_row"], "notes": r["notes"]}
            if (r["kind"] or "") == "party":
                party = {"col": r["hex_col"], "row": r["hex_row"]}
            else:
                out.append(d)
        return {"locations": out, "party": party}

    def set_party_position(self, col: int, row: int,
                           place: Optional[str] = None) -> Dict[str, Any]:
        self.repo.set_party_hex(self.cid, int(col), int(row))
        self.repo.record_event(
            self.cid, "map", "The party is at hex {},{}{}.".format(
                col, row, " (" + place + ")" if place else ""),
            in_game_date=self._date())
        out = {"party": {"col": int(col), "row": int(row)}, "at": place}
        # Arriving at a mapped settlement? Surface its market so the DM can offer
        # trade in-world (the player loves a living market on arrival).
        town, econ = self._current_economies()
        if econ:
            econs = self._econs(econ)
            out["settlement"] = town
            out["economies"] = econs
            try:
                out["goods_here"] = [g["good"] for g in
                                     trade_mod.available_goods(self.dice, econs)[:6]]
            except Exception:
                pass
            out["trade_prompt"] = ("A market trades here ({}). Offer it in-world "
                                   "-- stalls, a merchant calling wares -- and let "
                                   "them choose to deal; market_goods/buy_goods/"
                                   "sell_goods need no economy here, it is read "
                                   "from this town.").format(", ".join(econs))
        return out

    def seed_world(self) -> Dict[str, Any]:
        from engine.data import known_world
        n = known_world.seed_campaign(self.repo, self.cid)
        return {"seeded": n, "note": "The Known World's anchor locations placed."}

    def roll_ability(self, method: str = "4d6", count: int = 6) -> Dict[str, Any]:
        """Generate ability scores with the ENGINE's own roller -- the dice AND
        the drop are done by engine.dice, never the narrator. method: '3d6' |
        '4d6' (drop lowest) | '5d6' (drop the two lowest). Returns each score
        with its kept and dropped dice so the work is always shown."""
        rollers = {
            "3d6": self.dice.ability_3d6,
            "4d6": self.dice.ability_4d6_drop_lowest,
            "5d6": self.dice.ability_5d6_drop_two,
        }
        m = (method or "4d6").strip().lower()
        roller = rollers.get(m)
        if roller is None:
            return {"error": "unknown method {!r}; use '3d6', '4d6', or '5d6'".format(method),
                    "methods": sorted(rollers.keys())}
        n = max(1, min(int(count), 12))
        detail = []
        for _ in range(n):
            r = roller()
            detail.append({"score": r.natural, "kept": list(r.dice),
                           "dropped": list(r.dropped)})
        scores = sorted((d["score"] for d in detail), reverse=True)
        return {"method": m, "count": n, "scores": scores,
                "detail": detail, "total": sum(scores)}

    def _date(self) -> Optional[str]:
        c = self.repo.get_campaign(self.cid)
        cur = c["current_date"] if c else None
        # Heal a missing OR non-game date (e.g. a leaked real-world "2026-06-26")
        # back to the Known World default so display + advancement stay valid.
        if not cur or cal_mod.parse(cur) is None:
            cur = DEFAULT_START_DATE
            try:
                self.repo.set_date(self.cid, cur)
            except Exception:
                pass
        return cur

    # ---- world-building ------------------------------------------------
    def add_npc(self, name: str, race: str = "Human", role: str = "",
                alignment: str = "N", location: str = "", notes: str = "",
                char_class: Optional[str] = None, level: int = 1,
                hp_max: Optional[int] = None,
                ac_descending: int = 10) -> Dict[str, Any]:
        """Persist a named story NPC so they stay true next time -- a villager,
        innkeeper, merchant, patron, guard, or contact. Lightweight: a
        non-combatant needs no stats. Pass char_class (and optionally hp_max)
        only for an NPC who may fight or cast."""
        if not name or not name.strip():
            return {"error": "add_npc needs a name"}
        existing = self._find_char(name)
        if existing:
            return {"error": "{} is already on record".format(name),
                    "character_id": existing["id"]}
        classes = ([{"class": char_class, "level": int(level), "xp": 0}]
                   if char_class else [])
        detail = " -- ".join(p for p in (role, location, notes) if p)
        chid = self.repo.save_character(self.cid, {
            "name": name, "race": race, "classes": classes,
            "alignment": alignment, "hp_max": hp_max,
            "ac_descending": ac_descending, "notes": detail,
        }, is_npc=True)
        self.repo.record_event(
            self.cid, "npc",
            "{}{} entered the chronicle.".format(
                name, " ({})".format(role) if role else ""),
            in_game_date=self._date())
        return {"character_id": chid, "name": name, "race": race, "role": role,
                "location": location, "saved": True,
                "note": "{} is on record and will appear in CURRENT STATE next "
                        "turn.".format(name)}

    # ---- snapshot ------------------------------------------------------
    def _active_pc_name(self, prefer: Optional[str] = None) -> Optional[str]:
        """Pick the ACTIVE player character, not merely the first one created.
        Order: an explicit prefer= name; else the PC most recently named in the
        chronicle; else the most recently created PC; else the first."""
        try:
            rows = [r for r in self.repo.list_characters(self.cid)
                    if not r["is_npc"]]
        except Exception:
            rows = []
        if not rows:
            return None
        by_name = {r["name"]: r for r in rows}
        if prefer and prefer in by_name:
            return prefer
        # most recently referenced PC name in the recent chronicle
        try:
            low = {r["name"].lower(): r["name"] for r in rows}
            for e in reversed(list(self.repo.recent_events(self.cid, 50))):
                keys = e.keys() if hasattr(e, "keys") else []
                text = " ".join(str(e[k]) for k in keys
                                if k in ("summary", "detail", "detail_json")
                                and e[k]).lower()
                for lname, real in low.items():
                    if lname and lname in text:
                        return real
        except Exception:
            pass
        # else the most recently created PC (highest id)
        try:
            return max(rows, key=lambda r: r["id"])["name"]
        except Exception:
            return rows[0]["name"]

    def get_campaign_snapshot(self, recent: int = 12,
                              character: Optional[str] = None) -> Dict[str, Any]:
        """One consolidated read for resuming play in a fresh chat. Composed
        from the live tools/repo so it can never drift from the truth: PC sheet,
        memorized spells + slots, inventory, treasure, party position + current
        location, in-game date, NPCs, canon arcs, recent events, current scene."""
        def _safe(fn, *a, **k):
            try:
                return fn(*a, **k)
            except Exception as e:
                return {"error": "{}: {}".format(type(e).__name__, e)}

        chars_res = _safe(self.list_characters)
        chars = chars_res.get("characters", []) if isinstance(chars_res, dict) else []
        npcs = [c for c in chars if c.get("is_npc")]
        pc_name = self._active_pc_name(character)

        pc = _safe(self.get_character, pc_name) if pc_name else {}
        pc = pc if isinstance(pc, dict) else {}
        spells = _safe(self.spells_available, pc_name) if pc_name else {}
        advancement = _safe(self.get_advancement, pc_name) if pc_name else {}

        locs_res = _safe(self.list_locations)
        locations = locs_res.get("locations", []) if isinstance(locs_res, dict) else []
        party = locs_res.get("party", {}) if isinstance(locs_res, dict) else {}
        here = None
        if isinstance(party, dict):
            for L in locations:
                if L.get("col") == party.get("col") and L.get("row") == party.get("row"):
                    here = L
                    break

        events_res = _safe(self.recent_events, recent)
        events = events_res.get("events", []) if isinstance(events_res, dict) else []
        # recent_events is oldest->newest; the LATEST narration is the live scene.
        current_scene = next((e for e in reversed(events)
                              if e.get("kind") == "narration"), None)
        last_event = events[-1] if events else None
        last_saved_turn = (current_scene or last_event or {}).get("summary")

        canon_res = _safe(self.list_canon)
        canon = canon_res.get("canon", []) if isinstance(canon_res, dict) else []
        retainers = _safe(self.list_henchmen)

        # Campaign name + a monotonic version (total chronicle events) + a
        # real-world timestamp -- the at-a-glance "did the right save load?" check.
        camp_name = None
        try:
            camp = self.repo.get_campaign(self.cid)
            if camp is not None:
                camp_name = camp["name"] if "name" in camp.keys() else None
        except Exception:
            pass
        version = self._snapshot_version() or len(events)
        import datetime as _dt
        generated_at = _dt.datetime.now(_dt.timezone.utc).isoformat()

        # Where the party actually is, by name -- mapped location, else the
        # place label set on the party marker, else the bare hex.
        place = ((here or {}).get("name")
                 or (party.get("place") if isinstance(party, dict) else None)
                 or (("hex {},{}".format(party.get("col"), party.get("row")))
                     if isinstance(party, dict) and party.get("col") is not None
                     else None))

        return {
            "campaign": camp_name,
            "campaign_id": self.cid,
            "snapshot_version": version,
            "generated_at": generated_at,
            "date_time": self._date(),
            "place": place,
            "last_saved_turn": last_saved_turn,
            "pc": pc,
            "memorized_spells": {"memorized": pc.get("memorized", []), "slots": spells},
            "advancement": advancement,
            "inventory": pc.get("gear", []),
            "treasure": {"gold": pc.get("gold"), "goods": pc.get("gear", [])},
            "party": {"position": party, "retainers": retainers},
            "location": here or {"position": party, "note": "unmapped hex"},
            "locations_known": locations,
            "npcs": npcs,
            "canon": canon,
            "recent_events": events,
            "current_scene": current_scene,
        }

    def _snapshot_version(self) -> int:
        """Monotonic state version = total chronicle events for this campaign."""
        for _tbl in ("event", "events"):
            try:
                row = self.repo.conn.execute(
                    "SELECT COUNT(*) FROM {} WHERE campaign_id=?".format(_tbl),
                    (self.cid,)).fetchone()
                if row is not None:
                    return int(row[0])
            except Exception:
                continue
        return 0

    def campaign_resume(self, recent: int = 12,
                        character: Optional[str] = None) -> Dict[str, Any]:
        """THE single startup call. Returns the full world snapshot PLUS
        server_version, tool_capabilities (the domains the engine supports), and
        any active combat -- everything the referee needs to pick the game back
        up in a fresh chat, in one call. (domain_verb naming: dots are illegal in
        OpenAI-format tool names, so the convention is campaign_resume / combat_next.)"""
        snap = self.get_campaign_snapshot(recent=recent, character=character)
        if not isinstance(snap, dict):
            snap = {}
        # Capabilities, probed by a representative tool so the advertised list
        # can never drift from what the engine actually implements.
        probes = {
            "combat": "start_combat", "treasure": "generate_treasure",
            "travel": "journey", "merchant": "market_goods", "trade": "buy_goods",
            "spells": "cast_spell", "henchmen": "hire_henchman",
            "exploration": "random_encounter", "weather": "generate_weather",
            "domain": "found_dominion", "naval": "naval_battle",
            "magic_items": "roll_magic_item", "dungeon": "search",
        }
        snap["server_version"] = "0.9.0"
        snap["tool_capabilities"] = [
            d for d, probe in probes.items()
            if callable(getattr(self, probe, None))]
        active = None
        try:
            cs = self.combat_status()
            if isinstance(cs, dict) and not cs.get("error"):
                active = cs
        except Exception:
            pass
        snap["active_combat"] = active
        return snap

    def loot_bodies(self, names=None, group=None, to=None,
                    keep_bodies: bool = False) -> Dict[str, Any]:
        """Strip the fallen in ONE transaction -- the engine does all the math.
        Pools coin + gear off matching dead/dying NPCs, gives it to the PC, and
        returns the authoritative totals. Target with names=[...] or
        group=<name substring, e.g. 'Ghoul'>; omit both to loot every fallen NPC."""
        import collections
        listing = self.list_characters().get("characters", [])
        pc_name = to or next((c["name"] for c in listing if not c.get("is_npc")), None)
        if not pc_name:
            return {"error": "no recipient PC found; pass to=<name>"}

        ids = {}
        try:
            for r in self.repo.list_characters(self.cid):
                ids[r["name"]] = r["id"]
        except Exception:
            pass

        def _is_corpse(c):
            if not c.get("is_npc"):
                return False
            if c.get("alive") is False:
                return True
            if (c.get("status") or "").lower() in ("dead", "dying"):
                return True
            hp = c.get("hp")
            return isinstance(hp, (int, float)) and hp <= 0

        corpses = [c for c in listing if _is_corpse(c)]
        if names:
            want = {str(n).lower() for n in names}
            corpses = [c for c in corpses if c.get("name", "").lower() in want]
        elif group:
            g = str(group).lower()
            corpses = [c for c in corpses if g in c.get("name", "").lower()]
        if not corpses:
            return {"error": "no matching dead or dying bodies to loot",
                    "hint": "pass names=[...] or group='Ghoul', or omit both to loot all fallen"}

        total_gp = 0
        pieces = []
        looted = []
        for c in corpses:
            nm = c.get("name")
            sheet = self.get_character(nm)
            if not isinstance(sheet, dict) or sheet.get("error"):
                continue
            total_gp += int(sheet.get("gold") or 0)
            for it in (sheet.get("gear") or []):
                if isinstance(it, dict):
                    base = it.get("item", "item")
                    qty = int(it.get("qty", 1) or 1)
                    pieces += [base] * max(qty, 1)
                else:
                    pieces.append(str(it))
            looted.append(nm)

        recovered_items = []
        for disp, n in collections.Counter(pieces).items():
            recovered_items.append(disp if n == 1 else "{} x{}".format(disp, n))

        # transfer to the PC -- the engine computes the new total, not the caller
        pc_sheet = self.get_character(pc_name)
        pc_gold = int(pc_sheet.get("gold") or 0) if isinstance(pc_sheet, dict) else 0
        if total_gp:
            self.set_gold(pc_name, pc_gold + total_gp)
        for label in recovered_items:
            self.add_gear(pc_name, label)

        # clear the corpses so nothing is ever looted twice
        for nm in looted:
            chid = ids.get(nm)
            if keep_bodies:
                try:
                    self.set_gold(nm, 0)
                except Exception:
                    pass
            elif chid:
                try:
                    self.repo.delete_character(chid)
                except Exception:
                    pass

        try:
            self.repo.record_event(
                self.cid, "treasure",
                "Looted {} fallen: {} gp{}.".format(
                    len(looted), total_gp,
                    (" + " + ", ".join(recovered_items)) if recovered_items else ""),
                in_game_date=self._date())
        except Exception:
            pass

        return {"looted": True, "recipient": pc_name, "from": looted,
                "recovered_gp": total_gp, "recovered_items": recovered_items,
                "bodies_removed": (not keep_bodies)}

    # ---- registry ------------------------------------------------------
    def dispatch(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        fn = getattr(self, name, None)
        if not callable(fn) or name.startswith("_"):
            return {"error": "unknown tool {}".format(name)}
        try:
            result = fn(**(args or {}))
        except Exception as e:   # tools must never crash the turn
            return {"error": "{}: {}".format(type(e).__name__, e)}
        # Stamp the current snapshot id on EVERY response so the caller can
        # always tell whether its view of the world is stale.
        try:
            if isinstance(result, dict) and "snapshot_version" not in result:
                result["snapshot_version"] = self._snapshot_version()
        except Exception:
            pass
        return result


def specs() -> List[Dict[str, Any]]:
    """OpenAI-format tool schemas for the referee."""
    def t(name, desc, props, required=()):
        return {"type": "function", "function": {
            "name": name, "description": desc,
            "parameters": {"type": "object", "properties": props,
                           "required": list(required)}}}
    S = {"type": "string"}
    I = {"type": "integer"}
    cats = {"type": "string", "enum": list(saves_mod.CATEGORIES)}
    return [
        t("roll_dice", "Roll dice in standard notation, e.g. '1d20+2' or '3d6'.",
          {"notation": S}, ["notation"]),
        t("roll_ability", "Generate ability scores with the engine's OWN roller "
          "-- the dice and the drop are the engine's, not the narrator's. method "
          "'3d6' | '4d6' (drop lowest) | '5d6' (drop two); default 4d6, count 6. "
          "Returns each score with kept and dropped dice. Use for chargen.",
          {"method": S, "count": I}),
        t("recalc_ac", "Recompute and store a character's armour class from their "
          "worn armour, shield, and DEX (engine-owned). Runs automatically when "
          "armour is bought; call manually after dropping or swapping armour.",
          {"name": S}, ["name"]),
        t("lookup_rule", "Search the OSRIC rules (authoritative; matches the "
          "engine) for a procedure, class ability, or spell effect.",
          {"query": S}, ["query"]),
        t("lookup_lore", "Search the 1e reference corpus for setting lore, "
          "monsters, magic items, or deities (supplementary, not for mechanics).",
          {"query": S}, ["query"]),
        t("list_characters", "List the campaign's characters and NPCs.", {}),
        t("get_character", "Get one character's full sheet by name.",
          {"name": S}, ["name"]),
        t("add_npc", "Persist a named story NPC -- a villager, innkeeper, "
          "merchant, patron, guard, or contact -- so they stay on record and "
          "return next time. Call this the INSTANT you name someone the players "
          "might meet again. Non-combatants need no stats; pass char_class (and "
          "optionally hp_max) only for an NPC who may fight or cast. Put who they "
          "are, what they want, and any secret in notes.",
          {"name": S, "race": S, "role": S, "alignment": S, "location": S,
           "notes": S, "char_class": S, "level": I, "hp_max": I,
           "ac_descending": I}, ["name"]),
        t("saving_throw", "Roll a saving throw for a named character. category is "
          "one of the OSRIC save categories.",
          {"name": S, "category": cats, "modifier": I}, ["name", "category"]),
        t("attack", "Resolve one attack between two named characters; applies "
          "damage and updates the defender's HP. ONLY works inside a tracked "
          "combat (start_combat first) -- it records the attacker's action for "
          "the round. Pass weapon (a catalog name like 'Sword, long') to use its "
          "real damage -- automatically the 'vs Large+' die against big monsters -- "
          "and any specialisation bonus. The result reports attack_rate and "
          "attacks_this_round (a 7th+ level fighter gets 3/2; specialists more), so "
          "roll that many attacks. Use defender_size to override the target's size.",
          {"attacker": S, "defender": S, "situational": I, "damage_dice": S,
           "weapon": S, "defender_size": S}, ["attacker", "defender"]),
        t("set_weapon_specialisation", "Give a fighter/ranger/paladin weapon "
          "specialisation in an exact weapon (+1 to hit, +2 damage, improved "
          "attack rate; double=true for +3 damage on eligible melee weapons).",
          {"name": S, "weapon": S, "double": {"type": "boolean"}},
          ["name", "weapon"]),
        t("dual_class", "Begin dual-classing a human into a new class (needs 15+ "
          "in the old class's prime requisite and 17+ in the new one's). Keeps "
          "hit points, restarts at 1st level in the new class; all future XP go "
          "there, and the old class's abilities return once the new level passes "
          "the old.", {"name": S, "to_class": S}, ["name", "to_class"]),
        t("learn_spell", "A caster tries to add a spell to their spellbook. "
          "Arcane casters roll vs their Intelligence to understand it; divine "
          "casters succeed automatically. Costs 100 gp of ink per spell level. On "
          "success the spell is added to their book.",
          {"name": S, "spell": S, "spell_level": I}, ["name", "spell", "spell_level"]),
        t("research_spell", "Research a brand-new spell. Success = 10% (+10% per "
          "2000gp/level 'increment', up to +40%) + the caster's Int/Wis + their "
          "level - 2x the spell level. Costs 200gp/level + 1d4x100/week over "
          "(level+1) weeks (x10 facility cost if has_facility is false). Adds the "
          "spell on success.",
          {"name": S, "spell": S, "spell_level": I, "increments": I,
           "has_facility": {"type": "boolean"}}, ["name", "spell", "spell_level"]),
        t("scribe_scroll", "A level 7+ caster scribes a spell onto a scroll "
          "(50gp & 1 day per level, 20% failure -- 40% if overworked). Adds the "
          "scroll to their gear on success.",
          {"name": S, "spell": S, "spell_level": I,
           "overworked": {"type": "boolean"}}, ["name", "spell", "spell_level"]),
        t("brew_potion", "A level 7+ caster brews a potion: costs half its market "
          "value, one day per 50gp. Adds the potion to their gear.",
          {"name": S, "potion": S, "value_gp": I}, ["name", "potion", "value_gp"]),
        t("set_hp", "Set a character's current HP, and optionally their MAX HP "
          "(for familiar bonuses, temporary hit points, drain) and status. "
          "Setting hp_max lets later healing cap correctly.",
          {"name": S, "hp_current": I, "hp_max": I, "status": S},
          ["name", "hp_current"]),
        t("start_combat", "Begin a tracked combat and roll the first round's "
          "initiative. combatants is a list of {name, side ('party'/'foes'), "
          "action ('melee'/'missile'/'spell'), weapon (for its speed factor), "
          "casting_time (segments, for spells)}. Dexterity is read from each "
          "character's sheet. Lower segment acts first; the engine owns the order.",
          {"combatants": {"type": "array", "items": {"type": "object"}}},
          ["combatants"]),
        t("advance_turn", "Mark a combatant's NON-attack action for this round "
          "(they moved, cast a utility spell, defended, or fled). Required so the "
          "round can complete -- every living combatant must attack or advance_turn.",
          {"name": S, "note": S}, ["name"]),
        t("next_round", "Advance to the next combat round, re-rolling initiative "
          "(OSRIC re-rolls every round). REFUSES while any living combatant still "
          "has to act this round, so foes can't be skipped. Pass actions [{name, "
          "action, weapon, casting_time}] to change what someone does next round.",
          {"actions": {"type": "array", "items": {"type": "object"}}}),
        t("combat_status", "Show the active combat's round, initiative order, who "
          "has acted, and who still must act this round.", {}),
        t("stabilize", "Bind a dying character's wounds to stop the 1-hp/round "
          "bleeding (they stay unconscious until healed). A character is 'dying' "
          "from 0 to -9 hp and dies at -10.", {"name": S}, ["name"]),
        t("end_combat", "End the active combat.", {}),
        t("grant_xp", "Award experience. With a name, gives that character the "
          "XP; without a name, gives every player character that amount (the "
          "per-head share). The engine applies the +10% prime-requisite bonus if "
          "earned, splits XP across a multi-classed character's classes, looks up "
          "new levels in the OSRIC tables, rolls hit-point gains, and logs any "
          "level-ups. Never set levels by hand -- grant XP.",
          {"amount": I, "name": S}, ["amount"]),
        t("get_advancement", "Show a character's level(s), current XP, and XP "
          "remaining to the next level in each class.", {"name": S}, ["name"]),
        t("set_training_required", "Toggle the campaign's training rule. When on, "
          "earning enough XP doesn't level a character up -- the XP banks and they "
          "must train (time + gold) to gain the level.",
          {"on": {"type": "boolean"}}),
        t("train", "Train a character up one earned level: rolls the new level's "
          "hit points, charges 1,500 gp x current level, and advances the calendar "
          "1d3 weeks. Use after grant_xp reports ready_to_train.",
          {"name": S, "char_class": S}, ["name"]),
        t("advance_time", "Move the campaign calendar forward by N days and "
          "report the new date.", {"days": I}, ["days"]),
        t("rest", "Rest N days: advances the calendar and applies natural healing "
          "(1 hp/day, Constitution-adjusted; four weeks restores full). Name one "
          "character or rest the whole party.", {"days": I, "name": S}, ["days"]),
        t("set_proficiencies", "Set a character's proficient weapons. After this, "
          "attacking with a weapon NOT on the list takes the class non-proficiency "
          "penalty automatically (-2 fighter to -5 mage).",
          {"name": S, "weapons": {"type": "array", "items": S}}, ["name", "weapons"]),
        t("proficiency_slots", "How many weapon proficiencies a character gets by "
          "class and level, and which weapons they're proficient with.",
          {"name": S}, ["name"]),
        t("search", "Search a 10ft area for 'secret doors' (1 in 6; elves & "
          "half-elves 2 in 6) or 'traps' (2 in 6; dwarves & gnomes 3 in 6). The "
          "engine rolls -- don't decide if they find it.",
          {"name": S, "what": S}, ["name"]),
        t("listen_at_door", "Listen for noise (1 in 6; elves/gnomes/halflings/"
          "half-orcs 2 in 6). Thieves should use thief_skill 'listen' instead.",
          {"name": S}, ["name"]),
        t("force_door", "Force a stuck door (d6 vs the character's Strength "
          "open-doors number).", {"name": S}, ["name"]),
        t("bend_bars", "Bend bars / lift gates (d100 vs the character's Strength "
          "percentage).", {"name": S}, ["name"]),
        t("surprise_check", "Roll surprise for both sides at the start of an "
          "encounter (1d6 each, surprised on 1-2, Dexterity-adjusted). Pass the "
          "party names; foe_surprises_on raises the monsters' threshold.",
          {"party": {"type": "array", "items": S}, "foe_dex": I,
           "foe_surprises_on": I}),
        t("light_duration", "How long a light source lasts (torch 6 turns, etc.).",
          {"source": S}, ["source"]),
        t("thief_skill", "Roll a thief/assassin skill check (d100 vs the engine's "
          "level + Dexterity + ancestry chance). skill is one of: climb, hide, "
          "listen, pick_locks, pick_pockets, read_languages, move_quietly, traps "
          "(synonyms like 'open locks', 'move silently', 'hear noise' work). "
          "modifier is a situational +/-. Never guess the percentage.",
          {"name": S, "skill": S, "modifier": I}, ["name", "skill"]),
        t("turn_undead", "Resolve a Turn Undead attempt for a cleric or paladin "
          "against a kind of undead (by name -- skeleton, ghoul, wight, wraith, "
          "vampire... -- or 'Type N'). The engine reads the OSRIC turning table "
          "at the character's level, rolls, and reports how many are turned, "
          "destroyed, or (for evil clerics) controlled. number = how many undead "
          "are present, to cap those affected.",
          {"name": S, "undead": S, "number": I}, ["name", "undead"]),
        t("hire_henchman", "Take an NPC into a PC's service (creates the NPC and "
          "binds them as a retainer). status: conscript, hireling, follower, or "
          "henchman. Loyalty starts at 50 and shifts with the master's Charisma "
          "and the circumstance factors (relationship, training, payment, "
          "treatment, discipline, service). Warns if the master is over their "
          "Charisma henchman limit.",
          {"master": S, "name": S, "race": S, "char_class": S, "level": I,
           "hp": I, "status": S, "relationship": S, "training": S, "payment": S,
           "treatment": S, "discipline": S, "service": S}, ["master", "name"]),
        t("list_henchmen", "List a PC's retainers (or everyone's) with their "
          "current loyalty score and band.", {"master": S}),
        t("loyalty_check", "Test a retainer's loyalty (d100 vs adjusted loyalty). "
          "They give in to temptation / waver on a roll over their score. Use "
          "situational for the moment's stress (negative is harder).",
          {"name": S, "situational": I}, ["name"]),
        t("set_retainer", "Change a retainer's circumstances (payment, treatment, "
          "discipline, training, status, relationship, service) -- e.g. pay them "
          "late or treat them kindly -- and see the new loyalty.",
          {"name": S, "payment": S, "treatment": S, "discipline": S,
           "training": S, "status": S, "relationship": S, "service": S}, ["name"]),
        t("reaction_roll", "Roll an NPC's reaction (Table 1.6.2.8A) for "
          "negotiation or recruiting. Pass the negotiating PC's name to add their "
          "Charisma reaction modifier. situational is any extra +/-.",
          {"negotiator": S, "situational": I}),
        t("npc_morale", "Morale check for a hireling, henchman, or men-at-arms "
          "(d100 vs 50 + 5/HD + leader's loyalty bonus - situation). Reports "
          "holds, retreats, or surrenders.", {"name": S, "situational": I},
          ["name"]),
        t("spend_gold", "Deduct gold from a character (e.g. a purchase). Fails if "
          "they can't afford it.", {"name": S, "amount": I}, ["name", "amount"]),
        t("set_gold", "Set a character's gold to an exact amount.",
          {"name": S, "amount": I}, ["name", "amount"]),
        t("add_gear", "Add a free-text item to a character's gear/inventory (use "
          "add_equipment instead for catalog items, so it carries weight).",
          {"name": S, "item": S}, ["name", "item"]),
        t("remove_gear", "Remove an item from a character's gear/inventory.",
          {"name": S, "item": S}, ["name", "item"]),
        t("list_equipment", "Browse the OSRIC equipment catalog with weights, "
          "costs, weapon damage, and armour AC. category: weapon, armour, gear, "
          "or ammunition (omit for all).", {"category": S}),
        t("add_equipment", "Add a catalog item (weapon/armour/gear/ammunition) to "
          "a character, recording its weight so it counts toward encumbrance. "
          "qty for stacks; set pay=true to deduct its cost in gold (sub-gp totals "
          "round up to the nearest gp).",
          {"name": S, "item": S, "qty": I, "pay": {"type": "boolean"}},
          ["name", "item"]),
        t("encumbrance", "Total a character's carried weight (gear + coins), "
          "compare it to their Strength allowance, and report their encumbrance "
          "category and adjusted movement rate (armour caps included). Don't "
          "guess movement -- the engine computes it.", {"name": S}, ["name"]),
        t("poison_save", "Roll a character's save vs poison (uses their real save "
          "target). A failed save is fatal by default; give on_fail_damage / "
          "on_success_damage (e.g. '2d4') for poisons that wound instead of kill. "
          "Applies death or damage automatically.",
          {"name": S, "modifier": I, "on_fail_damage": S, "on_success_damage": S},
          ["name"]),
        t("disease_check", "Roll a save vs a disease/plague (vs poison). On a "
          "failure the engine rolls onset (2d8), the characteristic penalty "
          "(-1d6), duration (2d8), and whether it proves fatal. in_hours for an "
          "infected wound.", {"name": S, "modifier": I,
           "in_hours": {"type": "boolean"}}, ["name"]),
        t("drain_level", "Apply energy/level drain from undead (wight, wraith, "
          "spectre, vampire...). Removes the character's highest class level(s), "
          "drops their XP to the new level's start, reduces hit points, and slays "
          "them if drained below 1st. Never lower a level by hand -- use this.",
          {"name": S, "levels": I}, ["name"]),
        t("item_save", "Roll an item's saving throw vs a destructive effect when "
          "its bearer failed their own save. material: metal, wood, leather, "
          "cloth/rope, paper, stone/gem, crystal/glass, pottery/bone. attack: "
          "acid, cold, crushing, disintegrate, fall, fire (magical), normal fire, "
          "lightning. magic_bonus = the item's plus (0 for mundane).",
          {"material": S, "attack": S, "magic_bonus": I}, ["material", "attack"]),
        t("grapple", "Resolve an unarmed attack between two characters. mode: "
          "'grapple' (holds, mostly temporary damage) or 'overbear' (knock prone). "
          "The engine rolls the unarmed to-hit (by armour, Dexterity, movement) "
          "and the result table (Strength/size matter), and applies real damage. "
          "Optionally pass sizes (tiny/small/medium/large/huge/gargantuan).",
          {"attacker": S, "defender": S, "mode": S, "attacker_size": S,
           "defender_size": S}, ["attacker", "defender"]),
        t("spells_available", "How many spells a character may memorise per spell "
          "level (from the engine's slot tables, incl. Wisdom bonus).",
          {"name": S}, ["name"]),
        t("list_spells", "List the spells a class can choose at a given spell level.",
          {"char_class": S, "spell_level": I}, ["char_class", "spell_level"]),
        t("memorize_spell", "Memorise a spell into one of a character's slots. "
          "For a multi-class caster the engine routes the spell to whichever of "
          "their classes owns it; pass spell_class to disambiguate a shared spell. "
          "Fails only if that class has no free slot of the spell's level.",
          {"name": S, "spell": S, "spell_class": S}, ["name", "spell"]),
        t("cast_spell", "Cast a memorised spell. The engine resolves the "
          "mechanics: damage spells (Magic Missile, Fireball, Lightning Bolt, "
          "Cone of Cold, Flame Strike, Cause Wounds...) roll their dice scaled by "
          "caster level, roll each target's saving throw (half/negate), and apply "
          "the HP loss; healing spells (Cure Light/Serious/Critical) restore HP up "
          "to max; Sleep rolls creatures-affected by HD; Stinking Cloud rolls the "
          "save and rounds incapacitated. Pass targets (names) for offensive/heal "
          "spells. For spells with no hard numbers the engine returns the rules "
          "text to narrate -- you never invent the dice.",
          {"name": S, "spell": S, "targets": {"type": "array", "items": S},
           "caster_level": I, "save_mod": I}, ["name", "spell"]),
        t("get_monster", "Look up a monster's OSRIC stat block by name "
          "(AC, HD, attacks, morale, etc.).", {"name": S}, ["name"]),
        t("spawn_monster", "Spawn one or more of a monster as NPC combatants "
          "(rolls their HP) so the party can fight them with the attack tool. "
          "Use 'label' to name them (e.g. 'Goblin Sentry').",
          {"name": S, "label": S, "count": I}, ["name"]),
        t("generate_treasure", "Roll a treasure parcel for OSRIC loot classes "
          "(e.g. 'Hoard 3, Cache 4') -- coins, gems, jewellery, and magic-item "
          "counts. Use a monster's loot class or pick one for the hoard.",
          {"loot": S}, ["loot"]),
        t("roll_magic_item", "Roll one or more named magic items from the OSRIC "
          "catalog, optionally by category (potion, ring, rod/staff/wand, sword, "
          "weapon, armour, misc). Use after generate_treasure reports counts; "
          "then lookup_rule for the item's full effect.",
          {"category": S, "count": I}),
        t("random_encounter", "Roll a wandering monster for a terrain or dungeon "
          "depth (forest, hills, plains, mountains, swamp, desert, coast, "
          "dungeon-1, dungeon-2, dungeon-3). Returns the creature, number "
          "appearing, stats, AND the surprise roll and the monster's reaction "
          "(pass party names so Dexterity and Charisma count) -- a ready-made "
          "encounter. Group size is scaled by a rolled encounter CONTEXT "
          "(scouting patrol, hunting party, raiding warband, large band, full "
          "muster); pass context='lair' or a named context to force it. Roll by "
          "terrain (plains, forest, hills, marsh, scar, etc.) for The Known World. "
          "Then spawn_monster and start_combat.",
          {"terrain": S, "party": {"type": "array", "items": S},
           "foe_surprises_on": I, "context": S, "region": S, "subregion": S},
          ["terrain"]),
        t("generate_weather", "Generate the day's weather for a season (spring, "
          "summer, autumn, winter).", {"season": S}),
        t("list_vessels", "List cargo carriers (backpack to galleon) with "
          "capacity, cost, speed, and which terrain each can cross, plus "
          "available addons.", {}),
        t("set_vessel", "Assign a trader a cargo carrier (and optional addons) "
          "to set their cargo capacity for trade.",
          {"trader": S, "vessel_type": S, "addons": {"type": "array",
           "items": S}}, ["trader", "vessel_type"]),
        t("market_goods", "What's for sale at a settlement (comma-separated "
          "economies, e.g. 'Mining, Frontier'), with buy prices for the trader.",
          {"economies": S, "trader": S}, []),
        t("buy_goods", "Buy trade goods for a trader -- prices use their Charisma "
          "and the local economy; deducts gold and loads cargo (respecting vessel "
          "capacity).", {"trader": S, "good": S, "tons": I, "economies": S},
          ["trader", "good", "tons"]),
        t("sell_goods", "Sell a trader's cargo at the local economy -- prices use "
          "Charisma; adds gold and reports profit.",
          {"trader": S, "good": S, "tons": I, "economies": S},
          ["trader", "good", "tons"]),
        t("get_cargo", "Show a trader's cargo, total tonnage, and vessel capacity.",
          {"trader": S}, ["trader"]),
        t("list_titles", "The nobility ladder (Knight -> Emperor): what each "
          "grants and the cost to host one as a guest.", {}),
        t("build_stronghold", "Cost, build time, and engineers for a stronghold "
          "from {element: quantity} (e.g. Keep, Square / Wall, Castle / Gatehouse). "
          "region: normal, inaccessible (x2), or settled (half).",
          {"elements": {"type": "object"}, "region": S}, ["elements"]),
        t("found_dominion", "Establish a dominion for a ruler on a terrain "
          "(civ_level: wilderness/borderlands/civilized). Rolls settling families "
          "and resources, and the initial Confidence from the ruler's abilities.",
          {"ruler": S, "name": S, "terrain": S, "civ_level": S, "title": S,
           "has_liege": {"type": "boolean"}}, ["ruler", "name", "terrain"]),
        t("list_dominions", "List the campaign's dominions with population and "
          "confidence level.", {}),
        t("set_dominion_tax", "Set a dominion's poll-tax rate (gp/family). Raising "
          "it angers the populace (Confidence), lowering it pleases them.",
          {"dominion": S, "rate_gp": {"type": "number"}}, ["dominion", "rate_gp"]),
        t("dominion_events", "Roll a dominion's yearly events from the premade "
          "deck (1d4 of them, or a given count). Each draws a concrete event "
          "(bumper harvest, bandit raids, plague, a Power's patronage...) and "
          "applies its Confidence and population effects; income modifiers are "
          "reported for the next domain turn. The events are tabled, not invented.",
          {"dominion": S, "count": I}, ["dominion"]),
        t("domain_turn", "Run a dominion's monthly turn: income vs expenses "
          "(tithes, salt tax, troops, festivals), population growth, and bank the "
          "net into the ruler's purse. Confidence shapes how much is collected.",
          {"dominion": S, "festivals": I, "extra_expenses": I}, ["dominion"]),
        t("resolve_battle", "Resolve a mass battle (War Machine). Each side is an "
          "object: {name, troops, hit_dice, troop_class (untrained..elite), "
          "leader_level, leader_cha, mounted, missile, spellcasters, fortified}. "
          "Set siege=true to storm a fortified defender.",
          {"attacker": {"type": "object"}, "defender": {"type": "object"},
           "siege": {"type": "boolean"}, "attacker_terrain": I,
           "defender_terrain": I}, ["attacker", "defender"]),
        t("naval_battle", "Resolve ship-to-ship combat. Each ship is an object: "
          "{name, vessel_type (or tonnage), crew, crew_hd, crew_class, ram, "
          "artillery, leader_level, leader_cha}. Hull, ramming, artillery, and "
          "boarding decide who sinks, is captured, or holds the sea.",
          {"ship_a": {"type": "object"}, "ship_b": {"type": "object"},
           "ram_a": {"type": "boolean"}, "ram_b": {"type": "boolean"}},
          ["ship_a", "ship_b"]),
        t("journey", "Travel overland for N days through a terrain. Each day "
          "rolls weather, distance, getting-lost, and a wandering-monster check. "
          "Pass party (names) and the party automatically moves at its slowest, "
          "most-encumbered member's rate (the engine reads their gear and coin "
          "weight); otherwise give base_move. Returns a day-by-day log.",
          {"terrain": S, "days": I, "season": S, "base_move": I,
           "has_guide": {"type": "boolean"}, "party": {"type": "array", "items": S}},
          ["terrain"]),
        t("add_location", "Place or move a location on the Flanaess hex map. kind: "
          "city, town, dungeon, landmark, or region. terrain colours the hex "
          "(plains, forest, hills, mountains, desert, swamp, water, sea, coast).",
          {"name": S, "kind": S, "terrain": S, "col": I, "row": I, "notes": S},
          ["name", "col", "row"]),
        t("list_locations", "List mapped locations and the party's current hex.", {}),
        t("set_party_position", "Move the party marker to a hex (optionally name "
          "the place they've reached).",
          {"col": I, "row": I, "place": S}, ["col", "row"]),
        t("seed_world", "Place The Known World's anchor locations (Aurenholt, "
          "Valmoria City, Old Aurelis, Sahl-al-Brass, the home march of "
          "Halvedd...) onto a fresh campaign map.", {}),
        t("record_event", "Write a lasting event to the campaign chronicle.",
          {"summary": S, "kind": S}, ["summary"]),
        t("recent_events", "Read the most recent chronicle events.",
          {"limit": I}),
        t("define_canon", "Lock a canonical story truth -- an arc and its "
          "DEFINED boss, theme, weakness/win_condition, and clock.",
          {"slug": S, "title": S, "kind": S, "theme": S, "boss": S,
           "public": S, "secret": S, "win_condition": S, "clock": S,
           "status": S, "notes": S}, ["slug"]),
        t("get_canon", "Read a locked canon entry by slug. Sealed 'secret' DM "
          "truths are hidden unless reveal_secret=true.",
          {"slug": S, "reveal_secret": {"type": "boolean"}}, ["slug"]),
        t("list_canon", "List all locked story-canon entries.", {}),
        t("get_campaign_snapshot", "ONE consolidated read for resuming play in a "
          "fresh chat: the PC sheet, memorized spells and slots, inventory and "
          "treasure, party position and current location, in-game date, NPCs, "
          "canon arcs, recent events, and the current scene. 'recent' caps the "
          "event list; pass character=<name> to force which PC if several exist.",
          {"recent": I, "character": S}),
        t("campaign_resume", "THE single startup call -- call this FIRST to pick "
          "the game back up. Returns the full world snapshot PLUS server_version, "
          "tool_capabilities (the domains the engine supports), and any "
          "active_combat. You need nothing else before play. 'recent' caps the "
          "event list; pass character=<name> to force which PC if several exist.",
          {"recent": I, "character": S}),
        t("loot_bodies", "Strip the fallen in ONE transaction -- never do the "
          "arithmetic yourself. Pools coin and gear off matching dead/dying NPCs, "
          "gives it to the PC, and returns the authoritative totals "
          "(recovered_gp, recovered_items). Target with names=[...] or "
          "group='Ghoul' (name substring); omit both to loot ALL fallen NPCs. "
          "Emptied bodies are removed unless keep_bodies=true.",
          {"names": {"type": "array", "items": S}, "group": S, "to": S,
           "keep_bodies": {"type": "boolean"}}),
        t("travel_route", "Resolve an overland route read off the shared Darlene "
          "map -- the engine does all the distance/time math, you do none. Pass "
          "legs=[{terrain, hexes}] (or {terrain, miles}); the digital Darlene "
          "overlay is 6 miles/hex (miles_per_hex default 6). Uses the party's "
          "encumbered pace, sums the days, advances the calendar, and returns "
          "per-leg miles/days plus the arrival date. Pass party=[names] for "
          "true encumbered pace.",
          {"legs": {"type": "array", "items": {"type": "object"}},
           "miles_per_hex": I, "season": S, "base_move": I,
           "party": {"type": "array", "items": S},
           "advance": {"type": "boolean"}}, ["legs"]),
        t("add_venture", "Register/update a standing enterprise that pays "
          "monthly. yield_gp and upkeep_gp are PER MONTH; net = yield - upkeep. "
          "Upserts by slug; only the fields you pass change.",
          {"slug": S, "name": S, "kind": S, "location": S,
           "yield_gp": {"type": "number"}, "upkeep_gp": {"type": "number"},
           "status": S, "notes": S}, ["slug"]),
        t("list_ventures", "List standing ventures with monthly yield, upkeep, "
          "net, and the total net income per month.", {}),
        t("collect_ventures", "Pay out the accrued NET income of all active "
          "ventures over N months, crediting a character's gold.",
          {"months": {"type": "number"}, "deposit_to": S},
          ["months", "deposit_to"]),
    ]
