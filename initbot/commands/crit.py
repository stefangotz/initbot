from dataclasses import dataclass
from typing import List
from discord.ext import commands  # type: ignore

from ..utils import EqMatcher, Matcher, LoEMatcher, GoEMatcher, RangeMatcher
from .roll import DieRoll


@dataclass
class Crit:
    roll: Matcher
    effect: str


@dataclass
class CritTable:
    number: int
    crits: List[Crit]

    def match(self, roll: int) -> str:
        for crt in self.crits:
            if crt.roll.matches(roll):
                return crt.effect
        raise KeyError()


_CRITS_1 = [
    Crit(
        LoEMatcher(1),
        "Force of blow shivers your weapon free of your grasp. Inflict +1d6 damage with this strike and you are disarmed.",
    ),
    Crit(EqMatcher(2), "Opportunistic strike. Inflict +1d3 damage with this strike."),
    Crit(
        EqMatcher(2),
        "Foe jabbed in the eye! Ugly bruising and inflict +1d4 damage with this strike.",
    ),
    Crit(
        EqMatcher(3),
        "Stunning crack to forehead. Inflict +1d3 damage with this strike, and the foe falls to the bottom of the initiative count next round.",
    ),
    Crit(
        EqMatcher(4),
        "Strike to foe’s kneecap. Inflict +1d4 damage with this strike and the foe suffers a -10’ penalty to speed until healed.",
    ),
    Crit(EqMatcher(5), "Solid strike to torso. Inflict +1d6 damage with this strike."),
    Crit(
        EqMatcher(6),
        "Lucky strike disarms foe. You gain a free attack if the enemy stoops to retrieve his weapon.",
    ),
    Crit(
        EqMatcher(7),
        "Smash foe’s hand. Inflict +2d3 damage with this strike. You break two of the enemy’s fingers.",
    ),
    Crit(
        EqMatcher(8),
        "Numbing strike! Cursing in agony, the foe is unable to attack next round.",
    ),
    Crit(
        EqMatcher(9),
        "Smash foe’s nose. Inflict +2d4 damage with this strike and blood streams down the enemy’s face.",
    ),
    Crit(
        EqMatcher(10),
        "Foe trips on his own feet and falls prone for the remainder of the round.",
    ),
    Crit(EqMatcher(11), "Piercing strike. Inflict +2d4 damage with this strike."),
    Crit(
        EqMatcher(12),
        "Strike to groin. The foe must make a DC 15 Fort save or spend the next two rounds retching.",
    ),
    Crit(
        EqMatcher(13),
        "Blow smashes foe’s ankle; his movement speed is reduced by half.",
    ),
    Crit(EqMatcher(14), "Strike grazes temple; blood blinds the foe for1d3 rounds."),
    Crit(
        EqMatcher(15),
        "Stab enemy’s weapon hand. The weapon is lost and knocked 1d10+5 feet away.",
    ),
    Crit(
        EqMatcher(16),
        "Narrowly avoid foe’s counterstrike! Inflict normal damage and make another attack roll. If the second attack hits, you inflict an additional +1d6 damage.",
    ),
    Crit(
        EqMatcher(17),
        "Blow to throat. Foe staggers around for 2 rounds and is unable to speak, cast spells, or attack.",
    ),
    Crit(
        EqMatcher(18),
        "Foe falls into your attack. He takes +2d6 damage from the strike and curses your luck.",
    ),
    Crit(
        EqMatcher(19),
        "Miracle strike. The foe must make a DC 20 Fort save or fall unconscious.",
    ),
    Crit(
        GoEMatcher(20),
        "Lucky blow dents foe’s skull! Inflict +2d6 damage with this strike. If the foe has no helm, he suffers a permanent loss of 1d4 Int.",
    ),
]
_CRITS_2 = [
    Crit(LoEMatcher(0), "Miss! Hesitation costs you the perfect strike!"),
    Crit(
        EqMatcher(1),
        "Strike misses critical organs. Inflict a paltry +2d3 damage with this strike.",
    ),
    Crit(
        EqMatcher(2),
        "Slashes to head removes foe’s ear. Inflict +1d6 damage with this strike and leave the enemy with a nasty scar.",
    ),
    Crit(EqMatcher(3), "Clean strike to back. Inflict +2d6 damage with this strike."),
    Crit(
        EqMatcher(4),
        "Blow to chest staggers foe. You can make an immediate free attack.",
    ),
    Crit(
        EqMatcher(5),
        "Blow pierces foe’s kidneys. Inflict +3d3 damage with this strike, and the foe is stunned for 1 round.",
    ),
    Crit(
        EqMatcher(6),
        "Foe dazed by ferocious attack; his speed and actions are reduced by half.",
    ),
    Crit(
        EqMatcher(7),
        "Strike to chest grazes vital organ. Inflict +3d4 damage with this strike.",
    ),
    Crit(
        EqMatcher(8),
        "Strike cuts a line down foe’s face. He is blinded by blood for 1d4 rounds.",
    ),
    Crit(
        EqMatcher(9),
        "Foe stumbles over his own limbs, falling prone. Make another attack.",
    ),
    Crit(EqMatcher(10), "Masterful strike! Inflict +2d6 damage with this strike."),
    Crit(
        EqMatcher(11), "Strike severs larynx. Foe is reduced to making wet fish noises."
    ),
    Crit(
        EqMatcher(12),
        "Savage strike! Foe must succeed on a Fort save (DC 10 + PC level) or faint from the pain.",
    ),
    Crit(
        EqMatcher(13),
        "Foe disoriented by quick strikes. Foe suffers a -4 penalty to attack rolls for 1d4 rounds.",
    ),
    Crit(
        EqMatcher(14),
        "Strike to head. Foe must make a Fort save (DC 10 + PC level) or fall unconscious.",
    ),
    Crit(
        EqMatcher(15),
        "Blow drives foe to ground. Inflict +2d6 damage with this strike, and the enemy is knocked prone.",
    ),
    Crit(
        EqMatcher(16),
        "Lightning-fast shot to the face pops the foe’s eye like a grape. Foe is permanently blinded in one eye and can take no actions for 1d3 rounds.",
    ),
    Crit(
        EqMatcher(17),
        "Strike pierces lung. Inflict +2d6 damage with this strike, and the foe can take only one action on his next turn.",
    ),
    Crit(
        EqMatcher(18),
        "Devastating strike to back of head. Inflict +1d8 damage with this strike, and the foe must make a Fort save (DC 10 + PC level) or fall unconscious.",
    ),
    Crit(
        EqMatcher(19),
        "Attack severs major artery. Inflict +1d10 damage with this strike, and the foe must make a Fort save (DC 10 + PC level) or fall unconscious from shock and massive blood loss.",
    ),
    Crit(
        EqMatcher(20),
        "Throat slashed! Inflict +2d6 damage with this strike, and the foe must make a Fort save (DC 13 + PC level) or die in 1d4 rounds.",
    ),
    Crit(
        EqMatcher(21),
        "Strike pierces spinal column. Inflict +3d6 damage with this strike, and the foe must make a Fort save (DC 15 + PC level) or suffer paralysis.",
    ),
    Crit(
        EqMatcher(22),
        "Chest skewered, spearing a variety of organs. Inflict +2d6 damage with this strike, and the foe must make a Fort save (DC 13 + PC level) or die in 1d4 rounds.",
    ),
    Crit(
        EqMatcher(23),
        "Strike through ear canal enters the brain. Ear wax instantly removed, and the foe must make a Fort save (DC 15 + PC level) or die instantly. Inflict an extra +2d6 damage on successful save.",
    ),
    Crit(
        GoEMatcher(24),
        "Strike through heart! Inflict +3d6 damage with this strike, and the foe must make a Fort save (DC 20 + PC level) or die instantly.",
    ),
]
_CRITS_3 = [
    Crit(
        LoEMatcher(0),
        "Battle rage makes friend and foe indistinguishable. Foe is hit for +1d12 damage, and the ally nearest him is also hit by a rebounding blow for 1d4 damage. (A PC overcome by battle rage may temporarily expend points of his Personality or Intelligence score to enhance the damage on his critical hit. For every ability point he expends, he adds +1d12 to his damage roll.)",
    ),
    Crit(EqMatcher(1), "Savage attack! Inflict +1d6 damage with this strike."),
    Crit(
        EqMatcher(2), "Attack sweeps foe off his feet. Next round, the enemy is prone."
    ),
    Crit(EqMatcher(3), "Foe steps into attack. Inflict +1d8 damage with this strike."),
    Crit(
        EqMatcher(4), "Powerful strike hammers foe to his knees. Make another attack."
    ),
    Crit(
        EqMatcher(5),
        "Smash foe’s nose in an explosion of blood. Inflict +1d6 damage with this strike, and the foe loses his sense of smell for 1d4 hours.",
    ),
    Crit(
        EqMatcher(6),
        "Brutal strike to torso. Inflict +1d8 damage with this strike, and the foe suffers multiple broken ribs.",
    ),
    Crit(
        EqMatcher(7),
        "Strike to hand knocks weapon into the air. The weapon lands 1d20+5’ away.",
    ),
    Crit(
        EqMatcher(8),
        "Blow caroms off skull, deafening foe for 1d6 days. Inflict +1d6 damage with this strike.",
    ),
    Crit(
        EqMatcher(9),
        "Strike to leg splinters femur. Inflict +2d6 damage with this strike and foe loses 10’ of movement until healed.",
    ),
    Crit(EqMatcher(10), "Sunder foe’s weapon! Shards of metal fill the air.*"),
    Crit(
        EqMatcher(11),
        "Strike hammers foe’s belly causing massive internal bleeding. Unless he receives magical healing, the foe dies in 1d5 hours.",
    ),
    Crit(
        EqMatcher(12),
        "Blow to cranium staggers foe. The foe must make a Fort save (10 + PC level) or sink to floor, unconscious.",
    ),
    Crit(
        EqMatcher(13),
        "Strike breaks foe’s jaw. Blood and shattered teeth ooze down the foe’s face. Inflict +1d8 damage with this strike.",
    ),
    Crit(
        EqMatcher(14),
        "Attack hammers foe’s torso. Inflict +2d8 damage with this strike.",
    ),
    Crit(
        EqMatcher(15),
        "Strike dislocates shoulder! Inflict +1d8 damage and shield arm hangs loosely by muscle and skin; no AC bonus from shield.",
    ),
    Crit(
        EqMatcher(16),
        "Attack reduces foe’s attack hand to formless tissue; -4 penalty to future attacks.",
    ),
    Crit(EqMatcher(17), "Furious blows hammer target prone. Make another attack."),
    Crit(
        EqMatcher(18),
        "Blow hammers shards of bone into foe’s forebrain; gray matter oozes out. Inflict +1d8 damage with this strike, and the foe suffers 1d4 points of Int and Per loss.",
    ),
    Crit(
        EqMatcher(19),
        "Devastating strike to the chest. Inflict +2d8 damage with this strike.",
    ),
    Crit(
        EqMatcher(20),
        "Chest strike stuns foe for 1d3 rounds. Inflict +1d8 damage with this strike.",
    ),
    Crit(
        EqMatcher(21),
        "Strike to leg shatters femur, knocking foe to the ground. Foe’s movement drops by half. Inflict +2d8 damage with this strike and make another attack.",
    ),
    Crit(
        EqMatcher(22),
        "Weapon arm sundered by strike. The weapon is lost along with any chance of making an attack with this arm.",
    ),
    Crit(
        EqMatcher(23),
        "Blow craters skull. Inflict +2d8 damage with this strike, and the target permanently loses 1d4 Int and Per.",
    ),
    Crit(
        EqMatcher(24),
        "Masterful strike to throat. Inflict +2d8 damage with this strike and the foe staggers about gasping for air for 1d4 rounds.",
    ),
    Crit(
        EqMatcher(25),
        "Attack punches shattered ribs through lungs. Foe loses 50% of his remaining hit points and vomits copious amounts of blood.",
    ),
    Crit(
        EqMatcher(26),
        "Attack shatters foe’s face, destroying both eyes. Inflict +2d8 damage with this strike, and the foe is permanently blinded.",
    ),
    Crit(
        EqMatcher(27),
        "Crushing blow hammers chest. Inflict +3d8 damage with this strike, and the foe must make a Fort save (DC 15 + PC level) or be knocked unconscious.",
    ),
    Crit(
        GoEMatcher(28),
        "Blow destroys spinal column. Inflict +3d8 damage with this strike, and the foe must make a Fort save (DC 15 + PC level) or suffer paralysis.",
    ),
]
_CRITS_4 = [
    Crit(
        LoEMatcher(0),
        "Battle rage makes friend and foe indistinguishable. Foe is hit for +2d8 damage, and the ally nearest him is also hit by a rebounding blow for 1d4 damage. (A PC overcome by battle rage may temporarily expend points of his Personality or Intelligence score to enhance the damage on his critical hit. For every ability point he expends, he adds +1d12 to his damage roll.)",
    ),
    Crit(EqMatcher(1), "Herculean blow. Inflict +2d12 damage with this strike."),
    Crit(
        EqMatcher(2),
        "Ferocious strike leaves foe’s weapon hand dangling from the stump of a wrist. Inflict +1d12 damage with this strike.",
    ),
    Crit(
        EqMatcher(3),
        "Strike sweeps foe to the ground. Inflict +1d12 damage with this strike and make another attack on prone enemy.",
    ),
    Crit(
        EqMatcher(4),
        "Hammering blow drives nose cartilage into brain. Inflict +1d12 damage with this strike, and the foe suffers 1d6 Int loss.",
    ),
    Crit(
        EqMatcher(5),
        "Foe’s weapon shattered.* If the foe has no weapon, inflict +2d12 damage with this strike.",
    ),
    Crit(
        EqMatcher(6),
        "Strike shatters foe’s breastbone. The foe must make a Fort save (DC 15 + PC level) or fall unconscious as his internal organs collapse.",
    ),
    Crit(
        EqMatcher(7),
        "Foe driven back by furious assault. Inflict +2d12 damage with this strike, and the foe forgoes his next attack.",
    ),
    Crit(
        EqMatcher(8),
        "Concussive strike leaves foe dazed. Inflict +1d8 damage with this strike and make a second attack.",
    ),
    Crit(
        EqMatcher(9),
        "Blow to throat carries through to spinal column, reducing everything in between to pasty mush. Inflict +2d12 damage with this strike, and the foe loses speech for 1d4 weeks.",
    ),
    Crit(
        EqMatcher(10),
        "Blow craters temple. The foe must make a Fort save (DC 15 + PC level) or be blinded by pain and blood for 1d4 rounds.",
    ),
    Crit(
        EqMatcher(11),
        "Strike reduces face to a formless mass of flesh and bone fragments. Inflict +2d12 damage with this strike, and the foe has trouble making hard consonants.",
    ),
    Crit(
        EqMatcher(12),
        "You see red! Inflict +1d12 damage with this strike as you are overcome by battle rage! (A PC overcome by battle rage may temporarily expend points of his Personality or Intelligence score to enhance the damage on his critical hit. For every ability point he expends, he adds +1d12 to his damage roll.)",
    ),
    Crit(
        EqMatcher(13),
        "Hammering strike to torso crushes lesser organs into paste. Inflict +2d12 damage with this strike.",
    ),
    Crit(
        EqMatcher(14),
        "Blow to spinal column numbs lower limbs. The foe suffers a -4 penalty to AC as he learns to walk again.",
    ),
    Crit(
        EqMatcher(15),
        "Fearsome strike drives enemy to the blood-splattered floor. Foe cowers in fear, prone, for 1d4 rounds.",
    ),
    Crit(
        EqMatcher(16),
        "Blow shatters shield. Inflict +2d12 damage with this strike. If the foe has no shield, he is stunned by pain for 1d4 rounds.",
    ),
    Crit(
        EqMatcher(17),
        "Foe’s kneecap explodes into red mist. Foe’s movement drops to 0’, and you make another attack.",
    ),
    Crit(
        EqMatcher(18),
        "Frontal lobotomy. Inflict +1d12 damage with this strike, and the foe must make a Fort save (DC 15 + PC level) or suffer amnesia. The foe is stunned for 1d4 rounds, regardless.",
    ),
    Crit(
        EqMatcher(19),
        "Strike to weapon arm. Foe takes triple damage from his own weapon as it is hammered into his face. Foe drops weapon in dumbfounded awe.",
    ),
    Crit(
        EqMatcher(20),
        "Blow crushes spinal cord. Inflict +3d12 damage with this strike, and the foe must make a Fort save (DC 15 + PC level) or suffer permanent paralysis.",
    ),
    Crit(
        EqMatcher(21),
        "Blow reduces internal organs to jelly. Death is inevitable in 1d8 rounds.",
    ),
    Crit(
        EqMatcher(22),
        "Target is disemboweled, spilling his entrails onto the ground. The foe dies of shock in 1d6 rounds.",
    ),
    Crit(
        EqMatcher(23),
        "Strike to chest explodes heart. Inflict +3d12 damage with this strike, and the foe must make a Fort save (DC 15 + PC level) or die instantly.",
    ),
    Crit(
        GoEMatcher(24),
        "Skull crushed like a melon. Inflict +3d12 damage with this strike, and the foe must make a Fort save (DC 20 + PC level) or die in 1d3 rounds.",
    ),
]
_CRITS_5 = [
    Crit(
        LoEMatcher(0),
        "Battle rage makes friend and foe indistinguishable. Foe is hit for +3d8 damage, and the ally nearest him is also hit by a rebounding blow for 1d4 damage.",
    ),
    Crit(
        EqMatcher(1),
        "Foe’s weapon shattered.* If the foe has no weapon, inflict +3d12 damage with this strike.",
    ),
    Crit(
        EqMatcher(2),
        "Furious assault hurls foe back 1d10’. Any adjacent foes accidentally strike the target for damage.",
    ),
    Crit(
        EqMatcher(3),
        "Blow to skull destroys ear. Inflict +1d12 damage with this strike, and the foe suffers permanent deafness.",
    ),
    Crit(
        EqMatcher(4),
        "Strike to gut! The foe must make a Fort save (DC 20 + PC level) or spend the next 2 rounds retching bile from a ruptured stomach.",
    ),
    Crit(
        EqMatcher(5),
        "Foe casts weapon away and wails for mercy. Inflict +1d12 damage with this strike and make another attack.",
    ),
    Crit(
        EqMatcher(6),
        "Strike scalps foe. Blood courses down his face, and the foe is effectively blinded until healed.",
    ),
    Crit(
        EqMatcher(7),
        "Foe entangled on your weapon, reducing his AC by -6 while caught. Make another attack.",
    ),
    Crit(
        RangeMatcher(8, 12),
        "You see red! Inflict +1d12 damage with this strike as you are overcome by battle rage! (A PC overcome by battle rage may temporarily expend points of his Personality or Intelligence score to enhance the damage on his critical hit. For every ability point he expends, he adds +1d12 to his damage roll.)",
    ),
    Crit(
        RangeMatcher(13, 14),
        "Strike to weapon arm. Foe takes quadruple damage from his own weapon as it is hammered into his face. Foe drops weapon in dumbfounded awe.",
    ),
    Crit(
        EqMatcher(15),
        "Blow sunders shield. Inflict +2d12 damage with this strike. If the foe has no shield, he must make a Fort save (DC 20 + PC level) or be knocked unconscious from the pain.",
    ),
    Crit(
        EqMatcher(16),
        "Strike to top of skull shortens spinal column, shortening foe by 6”. Resulting nerve damage reduces foe’s AC by -4.",
    ),
    Crit(
        EqMatcher(17),
        "Target is disemboweled, spilling his entrails onto the ground. Foe dies instantly of shock.",
    ),
    Crit(
        EqMatcher(18),
        "Blow destroys target’s face. Foe is immediately rendered blind and deaf and is now capable of only wet, gurgling sounds.",
    ),
    Crit(
        EqMatcher(19),
        "Strike removes crown of target’s skull. Foe dies from exposed brain matter in 3d3 rounds.",
    ),
    Crit(
        EqMatcher(20),
        "Blow severs shield arm. Inflict +2d12 damage with this strike. Foe’s hopes of two-handed weapon mastery dashed.",
    ),
    Crit(
        EqMatcher(21),
        "Godly attack. Inflict +3d12 damage with this strike. If the target dies, move up to 10’ and make another attack on any foe within 10’.",
    ),
    Crit(
        EqMatcher(22),
        "Blow severs leg. Inflict +2d12 damage with this strike, and the foe’s movement drops to zero. Foe does nothing but wail in agony for 1d4 rounds.",
    ),
    Crit(
        EqMatcher(23),
        "Strike to skull stuns foe for 1d4+1 rounds and permanently reduces Int by 1d12. Make another attack on your inert foe.",
    ),
    Crit(
        EqMatcher(24),
        "Strike severs weapon arm. Inflict +2d12 damage with this strike, and the foe is disarmed, literally and figuratively.",
    ),
    Crit(
        EqMatcher(25),
        "Devastating strike to torso voids foe’s bowels and crushes organs into paste. Foe loses 50% of current hit points and all dignity.",
    ),
    Crit(
        EqMatcher(26),
        "Strike crushes throat. Foe begins drowning in his own blood and expires in 1d4 rounds.",
    ),
    Crit(
        EqMatcher(27),
        "Crippling blow to spine. Inflict +4d12 damage with this strike, and the foe suffers permanent paralysis.",
    ),
    Crit(
        GoEMatcher(28),
        "Foe decapitated with a single strike. You are Death incarnate. Continue to make attacks against any foes within 10’ until you miss.",
    ),
]

TABLES = [
    CritTable(1, _CRITS_1),
    CritTable(2, _CRITS_2),
    CritTable(3, _CRITS_3),
    CritTable(4, _CRITS_4),
    CritTable(5, _CRITS_5),
]


@dataclass
class Criticality:
    die: DieRoll
    table: CritTable


@commands.command()
async def crit(ctx, table: int, roll: int):
    await ctx.send(TABLES[table - 1].match(roll))


@crit.error
async def crit_error(ctx, error):
    await ctx.send(str(error))
