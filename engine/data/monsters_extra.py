"""monsters_extra.py -- bestiary entries the column-format ("variant") stat
blocks in the GM Guide split across side-by-side columns, which the line
extractor can't cleanly parse.

Transcribed by hand from those same GM Guide stat blocks (splitting each block's
columns into its named variants), in the same pipe-delimited shape as
monsters.txt. Covers the common combat monsters; a few highly-structured ones
(true dragons with breath weapons, dinosaurs, the four elementals at variable
HD, fiend nobility) are left to the lore lookup for now and can be added later.

Columns: name | hit_dice | armour_class | attacks | morale | size | no_enc | xp | intelligence | alignment | move
"""

EXTRA = [
    # --- ogres ---
    "Ogre | 4+1 | 5 [15] | 1 (1d10) or by weapon | 70 | Large (9ft+) |  | 95 +5/hp | Low (5-7) | Chaotic evil | 90ft",
    "Ogre Mage | 5+2 | 4 [16] | 1 (1d12) or by weapon | 75 | Large (9ft+) | 1 | 750 +6/hp | Average (8-10) | Chaotic evil | 90ft; 150ft flying",
    # --- bears ---
    "Bear, Black | 3+3 | 7 [13] | 2 claws (1d3) and 1 bite (1d6) | 65 | Medium | 1d3 | 75 +3/hp | Semi- (2-4) | Neutral | 120ft",
    "Bear, Brown | 5+5 | 6 [14] | 2 claws (1d6) and 1 bite (1d8) | 75 | Large (9ft) | 1d6 | 160 +6/hp | Semi- (2-4) | Neutral | 120ft",
    "Bear, Cave | 6+6 | 6 [14] | 2 claws (1d8) and 1 bite (1d12) | 80 | Large (12ft) | 1d2 | 225 +8/hp | Semi- (2-4) | Neutral | 120ft",
    "Bear, Polar | 8+8 | 6 [14] | 2 claws (1d10) and 1 bite (2d6) | 95 | Large (14ft) | 1d6 | 600 +12/hp | Semi- (2-4) | Neutral | 120ft",
    # --- wolves & dogs ---
    "Wolf | 2+2 | 7 [13] | 1 bite (1d4+1) | 60 | Small | 2d6 | 50 +2/hp | Semi- (2-4) | Neutral | 180ft",
    "Wolf, Dire | 3+3 | 6 [14] | 1 bite (2d4) | 65 | Medium | 1d4 | 75 +3/hp | Semi- (2-4) | Neutral | 180ft",
    # --- boars ---
    "Boar, Wild | 3+3 | 7 [13] | 1 tusk (3d4) | 70 | Medium | 1d12 | 75 +3/hp | Animal (1) | Neutral | 150ft",
    "Boar, Giant | 7 | 6 [14] | 1 tusk (3d6) | 75 | Large | 2d4 | 225 +8/hp | Animal (1) | Neutral | 120ft",
    # --- great cats ---
    "Lion | 5+3 | 5 [15] | 2 claws (1d6) and 1 bite (1d10) | 75 | Large | 2d6 | 250 +6/hp | Semi- (2-4) | Neutral | 120ft",
    "Mountain Lion | 3+2 | 6 [14] | 2 claws (1d4) and 1 bite (1d6) | 65 | Medium | 1d2 | 100 +3/hp | Semi- (2-4) | Neutral | 150ft",
    "Tiger | 5+5 | 6 [14] | 2 claws (1d6) and 1 bite (2d6) | 75 | Large | 1d4 | 250 +6/hp | Animal (1) | Neutral | 120ft",
    "Sabre-tooth Tiger | 7+2 | 6 [14] | 2 claws (1d8) and 1 bite (2d8) | 80 | Large | 1d4 | 525 +10/hp | Animal (1) | Neutral | 120ft",
    # --- giant vermin ---
    "Ant, Giant Worker | 2 | 3 [17] | 1 bite (1d6) | 55 | Small | 1d100 | 30 +1/hp | Animal (1) | Neutral | 180ft",
    "Ant, Giant Soldier | 3 | 3 [17] | 1 bite (2d4) and 1 sting (3d4) | 60 | Medium | 1d20 | 50 +2/hp | Animal (1) | Neutral | 180ft",
    "Beetle, Fire | 1+2 | 4 [16] | 1 bite (2d4) | 50 | Small | 3d6 | 30 +1/hp | Non- (0) | Neutral | 120ft",
    "Centipede, Giant | 1 hit point | 9 [11] | 1 bite (poison, save or weakened) | 45 | Small | 5d6 | 5 +1/hp | Non- (0) | Neutral | 150ft",
    "Spider, Giant | 4+4 | 4 [16] | 1 bite (2d4 + poison) | 70 | Large | 1d2 | 350 +5/hp | Low (5-7) | Chaotic evil | 120ft",
    # --- reptiles & amphibians ---
    "Frog, Giant | 4 | 5 [15] | 1 bite (2d6) | 65 | Large | 1d6 | 160 +6/hp | Animal (1) | Neutral | 30ft; 150ft swimming",
    "Lizard Man | 2+1 | 5 [15] | 2 claws (1d2) and 1 bite (1d8) or by weapon | 55 | Medium (7ft) | 10d4 | 20 +2/hp | Low (5-7) | Neutral | 60ft; 120ft swimming",
    "Snake, Giant Boa | 6+1 | 5 [15] | 1 bite (1d4) and 1 constrict (2d4) | 75 | Large | 1d2 | 345 +8/hp | Animal (1) | Neutral | 90ft",
    "Snake, Cobra | 4+2 | 5 [15] | 1 bite (1d3 + poison) | 65 | Large | 1d4 | 190 +4/hp | Animal (1) | Neutral | 120ft",
    # --- other beasts ---
    "Centaur | 4 | 5 [15] | 2 hooves (1d6) and 1 by weapon | 65 | Large | 4d6 | 75 +3/hp | Average (8-10) | Neutral good | 180ft",
    "Mobat | 4 | 2 [18] | 1 bite (2d4) | 70 | Medium | 1d8 | 75 +3/hp | Low (5-7) | Neutral evil | 30ft; 150ft flying",
    "Rat, Giant | 1d4 hit points | 7 [13] | 1 bite (1d3) | 50 | Small | 5d10 | 7 +1/hp | Semi- (2-4) | Neutral | 120ft",
    "Carrion Crawler | 3+1 | 3 [17] | 8 tentacles (paralysis) and 1 bite | 50 | Large | 1d6 | 105 +3/hp | Non- (0) | Neutral | 120ft",
    "Mammoth | 13 | 6 [14] | 2 tusks (2d6) and 1 trample (4d8) | 110 | Huge | 1d12 | 2,300 +17/hp | Animal (1) | Neutral | 150ft",
    "Roper | 11 | 0 [20] | 6 tentacles (weakness) and 1 bite (5d4) | 100 | Large | 1 | 2,700 +16/hp | Exceptional (15-16) | Chaotic evil | 30ft",
    # --- undead ---
    "Zombie | 2 | 8 [12] | 1 strike (1d8) | 50 | Medium | 3d4 | 30 +1/hp | Non- (0) | Neutral evil | 60ft",
    "Monster Zombie | 6 | 6 [14] | 1 strike (2d8) | 50 | Large | 1d4 | 145 +6/hp | Non- (0) | Neutral evil | 90ft",
    # --- aquatic ---
    "Sea Lion | 6 | 5 [15] | 2 claws (1d6) and 1 bite (2d6) | 75 | Large | 3d4 | 150 +6/hp | Semi- (2-4) | Neutral | 180ft swimming",
    "Squid, Giant | 12 | 3 [17] | 8 tentacles (1d6) and 1 bite (5d4) | 75 | Huge | 1 | 2,000 +16/hp | Non- (0) | Neutral | 180ft swimming",
    "Kraken | 20 | 5 [15] | 8 tentacles (3d6) and 1 bite | 145 | Huge | 1 | 17,500 +30/hp | Genius (17-18) | Neutral evil | 210ft swimming",
    # --- big nasties (single, but alternate AC tripped the filter) ---
    "Achaiyerai | 10 | 8 [12] | 1 bite (1d10) and 2 claws (1d8) | 90 | Huge | 1d6 | 1,400 +14/hp | Average (8-10) | Chaotic evil | 180ft",
    "Dark Creeper | 1+1 | 0 [20] | 1 dagger (1d4) | 55 | Small (4ft) | 1 | 50 +2/hp | Average (8-10) | Chaotic neutral | 90ft",
    "Dark Stalker | 2+1 | 0 [20] | 1 short sword (1d6) | 60 | Medium | 1 | 200 +3/hp | Average (8-10) | Chaotic neutral | 90ft",
    "Remorhaz | 10 | 0 [20] | 1 bite (6d6) | 80 | Huge | 1 | 7,000 +20/hp | Animal (1) | Neutral | 120ft",
    # --- apes & badgers ---
    "Ape (Gorilla) | 4 | 6 [14] | 2 fists (1d3) and 1 bite (1d6) | 65 | Medium | 3d6 | 110 +4/hp | Low (5-7) | Neutral | 120ft",
    "Ape, Carnivorous | 5 | 6 [14] | 2 fists (1d4) and 1 bite (1d8) | 70 | Large | 2d4 | 125 +4/hp | Low (5-7) | Neutral | 120ft",
    "Badger | 1+2 | 4 [16] | 2 claws (1d2) and 1 bite (1d3) | 55 | Small | 1d4 | 30 +1/hp | Semi- (2-4) | Neutral | 60ft; 30ft burrowing",
    "Badger, Giant | 3 | 4 [16] | 2 claws (1d3) and 1 bite (1d6) | 60 | Medium | 1d2 | 50 +2/hp | Semi- (2-4) | Neutral | 60ft; 30ft burrowing",
    # --- beasts & cattle ---
    "Bison | 5 | 7 [13] | 2 horns (1d8) | 70 | Large | 4d6 | 110 +4/hp | Animal (1) | Neutral | 150ft",
    "Bullywug | 1 | 6 [14] | 1 spear (1d6) or 1 bite (1d2) | 50 | Medium | 2d4 | 18 +1/hp | Low (5-7) | Chaotic evil | 30ft; 150ft swimming",
    "Warhorse, Heavy | 3+3 | 7 [13] | 2 hooves (1d8) and 1 bite (1d3) | 60 | Large | 1 | 20 +2/hp | Animal (1) | Neutral | 150ft",
    # --- giant insects ---
    "Beetle, Boring | 5 | 3 [17] | 1 bite (5d4) | 50 | Large | 3d6 | 110 +4/hp | Non- (0) | Neutral | 60ft",
    "Beetle, Stag | 7 | 3 [17] | 1 bite (4d4) and 1 horn (1d10) | 50 | Large | 2d6 | 225 +8/hp | Non- (0) | Neutral | 60ft",
    "Fly, Giant | 3 | 6 [14] | 1 bite (1d8+1) | 50 | Medium | 1d8 | 40 +3/hp | Non- (0) | Neutral | 90ft; 300ft flying",
    "Fly, Giant Horsefly | 6 | 5 [15] | 1 bite (2d6) | 50 | Large | 1d8 | 165 +6/hp | Non- (0) | Neutral | 90ft; 300ft flying",
    # --- chimerae & crustaceans ---
    "Chimera | 9 | 4 [16] | 2 claws (1d4), 2 horns (1d3) and 1 bite (3d4) | 90 | Large | 1d4 | 1,300 +12/hp | Semi- (2-4) | Chaotic evil | 90ft; 180ft flying",
    "Gorgimera | 10+1 | 3 [17] | 2 claws (1d4), 2 horns (1d6) and 1 bite (2d6) | 95 | Large | 1 | 2,250 +14/hp | Semi- (2-4) | Chaotic evil | 120ft; 150ft flying",
    "Crab, Giant | 3 | 3 [17] | 2 pincers (2d4) | 50 | Large | 1d2 | 75 +3/hp | Non- (0) | Neutral | 90ft",
    "Crayfish, Giant | 4+4 | 4 [16] | 2 pincers (2d6) | 50 | Large | 1d2 | 110 +4/hp | Non- (0) | Neutral | 60ft; 120ft swimming",
    # --- genies & elementals ---
    "Djinni | 7+3 | 4 [16] | 1 slam (2d8) | 85 | Large (8ft) | 1 | 650 +10/hp | Average (8-10) | Chaotic good | 90ft; 240ft flying",
    "Djinni, Noble | 10 | 4 [16] | 1 slam (3d8) | 95 | Large (8ft) | 1 | 1,200 +13/hp | High (13-14) | Chaotic good | 90ft; 240ft flying",
    "Elemental, Air | 8 | 2 [18] | 1 strike (2d10) | 50 | Large | 1 | 1,200 +10/hp | Low (5-7) | Neutral | 360ft flying",
    "Elemental, Earth | 8 | 2 [18] | 1 strike (4d8) | 50 | Large | 1 | 1,200 +10/hp | Low (5-7) | Neutral | 60ft",
    "Elemental, Fire | 8 | 2 [18] | 1 strike (3d8) | 50 | Large | 1 | 1,200 +10/hp | Low (5-7) | Neutral | 120ft",
    "Elemental, Water | 8 | 2 [18] | 1 strike (3d8) | 50 | Large | 1 | 1,200 +10/hp | Low (5-7) | Neutral | 60ft; 180ft swimming",
    # --- elephants & big fish ---
    "Elephant | 11 | 6 [14] | 2 tusks (2d6) and 1 trample (4d8) | 100 | Huge | 1d12 | 1,400 +14/hp | Animal (1) | Neutral | 150ft",
    "Mastodon | 12 | 6 [14] | 2 tusks (2d6) and 1 trample (4d8) | 105 | Huge | 1d12 | 1,900 +16/hp | Animal (1) | Neutral | 150ft",
    "Fish, Giant Gar | 8 | 3 [17] | 1 bite (2d10) | 50 | Large | 1d6 | 575 +4/hp | Non- (0) | Neutral | 300ft swimming",
    "Fish, Giant Pike | 4 | 5 [15] | 1 bite (3d6) | 50 | Large | 1d8 | 90 +4/hp | Non- (0) | Neutral | 300ft swimming",
    "Leviathan | 24 | 6 [14] | 1 bite (5d4) | 50 | Huge | 1 | 5,000 +24/hp | Non- (0) | Neutral | 300ft swimming",
    # --- lizards, mephits, molds, nagas ---
    "Lizard, Giant | 3+1 | 5 [15] | 1 bite (1d8) | 50 | Large | 2d6 | 120 +4/hp | Non- (0) | Neutral | 150ft",
    "Lizard, Monitor | 8 | 5 [15] | 1 bite (2d6) | 50 | Huge | 1d6 | 925 +10/hp | Non- (0) | Neutral | 60ft",
    "Mephit, Fire | 3+1 | 5 [15] | 2 claws (1d3 + fire) | 60 | Medium (5ft) | 1 | 155 +4/hp | Average (8-10) | Any evil | 120ft; 240ft flying",
    "Mephit, Steam | 3+3 | 7 [13] | 2 claws (1d3 + steam) | 65 | Medium (5ft) | 1 | 170 +4/hp | Average (8-10) | Any evil | 120ft; 240ft flying",
    "Yellow Mold | 1 | 10 [10] | spores (save vs poison) | N/A | Small to Large | 1 | 35 +1/hp | Non- (0) | Neutral | 0",
    "Naga, Guardian | 11 | 3 [17] | 1 bite (1d6) and tail lash (2d8) | 100 | Large | 1d2 | 3,500 +10/hp | Exceptional (15-16) | Lawful good | 150ft",
    "Naga, Spirit | 9 | 4 [16] | 1 bite (1d3 + poison) | 90 | Large | 1d3 | 2,750 +14/hp | High (13-14) | Chaotic evil | 120ft",
    "Naga, Water | 7 | 5 [15] | 1 bite (1d4 + poison) | 80 | Medium | 1d4 | 1,350 +10/hp | Very (11-12) | Neutral | 90ft swimming",
    # --- aberrations, aquatic folk, more snakes ---
    "Otyugh | 7 | 3 [17] | 2 tentacles (1d8) and 1 bite (1d4+2) | 80 | Large | 1d2 | 650 +8/hp | Low (5-7) | Neutral | 60ft",
    "Sahuagin | 2+2 | 5 [15] | 2 claws (1d4) and 1 bite (1d4) or by weapon | 55 | Medium | 1d100 | 30 +3/hp | High (13-14) | Lawful evil | 120ft; 240ft swimming",
    "Snake, Amphisbaena | 6 | 3 [17] | 1 bite (1d3 + poison) | 75 | Medium (6ft) | 1d3 | 475 +6/hp | Animal (1) | Neutral | 120ft",
    "Eel, Giant | 5 | 6 [14] | 1 bite (3d6) | 50 | Large | 1 | 110 +4/hp | Non- (0) | Neutral | 90ft swimming",
    # --- dragons (representative ADULT stats; age categories, hit points, and
    #     breath-weapon specifics live in the GM Guide -> use lookup_rule).
    "Dragon, White | 6 | 3 [17] | 2 claws (1d4) and 1 bite (2d8); breath cold cone | 75 | Huge | 1d4 | 1,400 +8/hp | Semi- (2-4) | Chaotic evil | 90ft; 240ft flying",
    "Dragon, Black | 7 | 3 [17] | 2 claws (1d4) and 1 bite (3d6); breath acid line | 80 | Huge | 1d4 | 1,900 +10/hp | Low (5-7) | Chaotic evil | 90ft; 240ft flying",
    "Dragon, Green | 8 | 2 [18] | 2 claws (1d6) and 1 bite (2d10); breath chlorine cloud | 85 | Huge | 1d4 | 2,400 +12/hp | Average (8-10) | Lawful evil | 90ft; 240ft flying",
    "Dragon, Blue | 9 | 2 [18] | 2 claws (1d6) and 1 bite (3d10); breath lightning line | 90 | Huge | 1d4 | 3,200 +14/hp | Very (11-12) | Lawful evil | 90ft; 240ft flying",
    "Dragon, Red | 10 | -1 [21] | 2 claws (1d8) and 1 bite (3d10); breath fire cone | 95 | Huge | 1d4 | 4,800 +16/hp | Exceptional (15-16) | Chaotic evil | 90ft; 240ft flying",
    "Dragon, Brass | 7 | 2 [18] | 2 claws (1d4) and 1 bite (3d4); breath sleep gas or fire | 80 | Huge | 1d4 | 1,900 +10/hp | Average (8-10) | Chaotic neutral | 90ft; 240ft flying",
    "Dragon, Copper | 8 | 0 [20] | 2 claws (1d6) and 1 bite (3d6); breath acid line or slow gas | 85 | Huge | 1d4 | 2,400 +12/hp | Very (11-12) | Chaotic good | 90ft; 240ft flying",
    "Dragon, Bronze | 9 | 0 [20] | 2 claws (1d6) and 1 bite (4d6); breath lightning or repulsion gas | 90 | Huge | 1d4 | 3,200 +14/hp | Exceptional (15-16) | Lawful good | 90ft; 240ft flying",
    "Dragon, Silver | 10 | -1 [21] | 2 claws (1d6) and 1 bite (5d6); breath cold cone or paralysis gas | 95 | Huge | 1d4 | 4,800 +16/hp | Exceptional (15-16) | Lawful good | 90ft; 240ft flying",
    "Dragon, Gold | 11 | -2 [22] | 2 claws (1d8) and 1 bite (6d6); breath fire or chlorine gas | 100 | Huge | 1d4 | 6,400 +18/hp | Genius (17-18) | Lawful good | 90ft; 240ft flying",
    # --- iconic fiend (read from the GM Guide demon section) ---
    "Balor (Class F Demon) | 8+8 | -2 [22] | 1 sword +1 (1d12) or 1 whip (1d6 + fire) | 95 | Large (12ft) | 1d3 | 3,600 +12/hp | High (13-14) | Chaotic evil | 60ft; 150ft flying",
    # --- more giant insects / vermin ---
    "Beetle, Bombardier | 2+2 | 4 [16] | 1 bite (2d6) | 50 | Medium | 3d4 | 65 +2/hp | Non- (0) | Neutral | 90ft",
    "Beetle, Water | 4 | 3 [17] | 1 bite (3d6) | 50 | Medium | 1d12 | 75 +3/hp | Non- (0) | Neutral | 30ft; 120ft swimming",
    "Beetle, Death Watch | 9+1 | 3 [17] | 1 bite (3d4) | 50 | Large | 1 | 1,100 +12/hp | Non- (0) | Neutral | 120ft",
    "Beetle, Rhinoceros | 12 | 2 [18] | 1 bite (2d8) and 1 horn (3d8) | 50 | Large | 1d6 | 1,300 +6/hp | Non- (0) | Neutral | 60ft",
    "Wasp, Giant | 4 | 4 [16] | 1 sting (1d3 + poison) and 1 bite (1d8) | 50 | Medium | 1d4 | 150 +5/hp | Non- (0) | Neutral | 60ft; 180ft flying",
    "Bee, Giant Bumblebee | 6+4 | 5 [15] | 1 sting (1d6 + poison) | 80 | Medium | 1d4 | 300 +8/hp | Non- (0) | Neutral | 60ft; 240ft flying",
    "Centipede, Giant Huge | 3 | 5 [15] | 1 bite (1d3 + poison) | 45 | Medium | 1d4 | 125 +3/hp | Non- (0) | Neutral | 180ft",
    "Ant, Giant Queen | 10 | 4 [16] | 1 bite (2d4) | 50 | Large | 1 | 700 +13/hp | Low (5-7) | Neutral | 30ft",
    # --- more beasts ---
    "Bull | 4 | 7 [13] | 2 horns (1d6) | 65 | Large | 1 | 75 +3/hp | Animal (1) | Neutral | 150ft",
    "Rhinoceros | 8 | 6 [14] | 1 gore (2d4) | 50 | Large | 1d12 | 550 +10/hp | Animal (1) | Neutral | 120ft",
    "Rhinoceros, Woolly | 10 | 5 [15] | 1 gore (2d6) | 95 | Large | 1d6 | 900 +12/hp | Animal (1) | Neutral | 120ft",
    "Bat, Giant | 2 | 8 [12] | 1 bite (1d4) | 50 | Small | 1d10 | 20 +2/hp | Animal (1) | Neutral | 30ft; 150ft flying",
    "Eagle, Giant | 4 | 7 [13] | 2 talons (1d6) and 1 bite (2d6) | 65 | Large | 1d6 | 105 +4/hp | Average (8-10) | Neutral good | 30ft; 480ft flying",
    "Toad, Giant | 2+4 | 6 [14] | 1 bite (2d4) | 60 | Medium | 1d4 | 20 +2/hp | Animal (1) | Neutral | 60ft; 60ft leaping",
    "Snake, Pit Viper | 4+2 | 5 [15] | 1 bite (1d3 + poison) | 65 | Large | 1d6 | 155 +4/hp | Animal (1) | Neutral | 150ft",
    "Eel, Weed | 2 | 9 [11] | 1 bite (1d4) | 50 | Medium | 1 | 40 +2/hp | Non- (0) | Neutral | 120ft",
    "Eel, Electric | 1d6 hit points | 8 [12] | 1 bite (1d3) and shock | 50 | Small | 1 | 30 +1/hp | Non- (0) | Neutral | 120ft",
    # --- elemental-kin & aberrations ---
    "Lizard, Fire | 10 | 3 [17] | 2 claws (1d8) and 1 bite (2d6) | 95 | Huge | 1d4 | 1,500 +14/hp | Animal (1) | Neutral | 90ft",
    "Lizard, Cave | 6 | 5 [15] | 1 bite (1d8) | 50 | Large | 1d6 | 375 +6/hp | Non- (0) | Neutral | 120ft",
    "Mephit, Lava | 3 | 6 [14] | 2 claws (1d3 + lava) | 60 | Medium (5ft) | 1 | 110 +3/hp | Average (8-10) | Any evil | 120ft; 240ft flying",
    "Mephit, Smoke | 3 | 4 [16] | 2 claws (1d3 + smoke) | 60 | Medium (5ft) | 1 | 100 +3/hp | Average (8-10) | Any evil | 120ft; 240ft flying",
    "Brown Mold | 1 | 10 [10] | cold drain (save vs poison) | N/A | Small to Large | 1 | 30 +1/hp | Non- (0) | Neutral | 0",
    "Neo-Otyugh | 11 | 0 [20] | 2 tentacles (2d6) and 1 bite (1d3) | 90 | Large | 1 | 2,400 +14/hp | Very (11-12) | Neutral | 60ft",
]
