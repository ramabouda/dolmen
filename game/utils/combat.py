#vim: set fileencoding=utf-8 :
from collections import Counter
from django.template.loader import render_to_string
from random import choice, randint, shuffle
from game.models import UnitType


ROUND_MAX = 3
SEUIL_KO = 60 #in %


class FightingUnitType:
    """ keeps the stat of a unit for a tribe"""
    unit_type = ''
    attack = 0
    defense = 0
    HP_max = 0
    
    def __init__(self, unit_type, tribe=None, opponent_tribe=None):
        self.unit_type = unit_type
        self.attack = unit_type.compute_attack(tribe, opponent_tribe)
        self.defense = unit_type.compute_defense(tribe, opponent_tribe)
        self.HP_max = self.defense*3

class FightingUnit:
    fighting_unit_type = None
    HP_left = 0
    
    def __init__(self, fighting_unit_type):
        self.fighting_unit_type = fighting_unit_type
        self.HP_left = fighting_unit_type.HP_max
        
    def hit_unit(self, unit):
        """ hit the given unit """
        unit.HP_left -= self.fighting_unit_type.attack

    def check_state(self):
        """
        Return :
        OK : continues fighting
        dead : rip
        wounded : retires from the fight
        """
        
        if self.HP_left <= 0:
            return 'dead'
        elif self.HP_left < self.fighting_unit_type.HP_max*SEUIL_KO/100:
            coeff_coward=1
            if self.fighting_unit_type.unit_type.identifier == 'coward':
                coeff_coward=1.5
            if randint(0, SEUIL_KO)*coeff_coward > (self.HP_left*100 // self.fighting_unit_type.HP_max):
                return 'wounded'
        return 'OK'

class Combat:
    """
    Chaque unité est appariée avec une autre pour former des paires de combat.
    Les combattants en excès sont assignés au hasard à une des paires ayant le
    moins de combattants.
    A chaque round, les unités de chaque paire portent une attacknt à l'adversaire.
    Si il y a plus d'un adversaire, l'attack sera répartie au hasard.
    
    Quand une unité a un % de PV en dessous de son seuil de KO, elle a des
    chances de tomber KO ou de fuir le combat.
    A 0 PV, les unités sont définitivement mortes
    """
    
    def __init__(self, attackers, defenders):
        """
        attackers and defenders are Group objects
        
        In this class,
        units are FightingUnit objects
        unit types are FightingUnitType objects
        """

        #list of dict containing pairs of "attacker" and "defender" unit lists
        self.pairs = []
        #list of FightingUnitType objects
        self.unit_types_attacker = {}
        self.unit_types_defender = {}
        #record the lists of units at the end of each round for reports
        self.record_rounds = []
        #lists of FightingUnit
        self.units_attacker = []
        self.units_defender = []
        self.units_dead_attacker = []
        self.units_dead_defender = []
        self.units_fleeing_attacker = []
        self.units_fleeing_defender = []
        #nicely presented results
        self.attack_deads = Counter()
        self.attack_fleeing = Counter()
        self.defense_deads = Counter()
        self.defense_fleeing = Counter()
        #all the units that are not deads, including the fleeing ones
        self.attack_remain = Counter()
        self.defense_remain = Counter()
        #number min of fighters in a combat pair on the most numerous side
        self.pair_number_min_fighters = 1
        self.current_round = 1
        self.report = ''
        self.round_per_round = ''

        #units at the beginning of the flight
        self.units_attacker_count = {
                stack.unit_type: stack.number
                for stack in attackers.unitstack_set.all()}
        self.units_defender_count = {
                stack.unit_type: stack.number
                for stack in defenders.unitstack_set.all()}
        
        unit_types = UnitType.objects.filter(name__in = \
            [u.unit_type.name for u in attackers.unitstack_set.all()])        
        #unit profile creation
        for u in unit_types:
            #attacker
            try:
                attackers_tribe = self.attackers.village.tribe
            except AttributeError:
                attackers_tribe = None                
            self.unit_types_attacker[u.name] = (FightingUnitType(
                unit_type=u,
                tribe=attackers_tribe,
                #FIXME opponent_tribe=defenders.get_tribe()
                opponent_tribe=None
            ))
            
        unit_types = UnitType.objects.filter(name__in = \
            [u.unit_type.name for u in defenders.unitstack_set.all()])    
        #unit profile creation
        for u in unit_types:
            #defender
            try:
                defenders_tribe = self.defenders.village.tribe
            except AttributeError:
                defenders_tribe = None                
            self.unit_types_defender[u.name] = (FightingUnitType(
                unit_type=u,
                tribe=defenders_tribe,
                #FIXME opponent_tribe=defenders.get_tribe()
                opponent_tribe=None
            ))
            
        #creation of each unit
        for stack in attackers.unitstack_set.all():
            fighting_unit_type = (self.unit_types_attacker[stack.unit_type.name])
            for i in xrange(0, stack.number):
                self.units_attacker.append(FightingUnit(fighting_unit_type))
        for stack in defenders.unitstack_set.all():
            fighting_unit_type = (self.unit_types_defender[stack.unit_type.name])
            for i in xrange(0, stack.number):
                self.units_defender.append(FightingUnit(fighting_unit_type))
        
        self.nb_attackers = len(self.units_attacker)
        self.nb_defenders = len(self.units_defender)
        
        self.build_pairs(self.units_attacker, self.units_defender)
        self.fight()
        self.present_results()
        self.make_report()

    def build_pairs(self, units_attacker, units_defender):
        """ Build the pairs of fighters with the given lists of FightingUnit"""
        
        #shuffle the units
        shuffle(units_attacker)
        shuffle(units_defender)
            
        #build pairs
        for i in xrange(0, max(len(units_attacker), len(units_defender))):
            #get an attacker
            try:
                u_attacker=units_attacker[i]
            except IndexError:
                u_attacker=None
            #get a defender
            try:
                u_defender=units_defender[i]
            except IndexError:
                u_defender=None
                
            self.pair_units(u_attacker, u_defender)

    def pair_units(self, u_attacker=None, u_defender=None):
        """
        pair units together to fight
        if one of the units is not given, the other will be assigned to another pair
        
        returns True if a unit has been assigned, False if no units are given
        """
        #no more units
        if u_attacker is None and u_defender is None:
            return False
        #left only attackers
        elif u_attacker is None:
            #pair the defender with an attacking reinforcement, if possible
            max_pair = self.get_pair_max_reinforcements()
            if max_pair :
                self.pair_units(max_pair['attacker'].pop(), u_defender)
            #attacker added as reinforcement
            else:
                self.pair_side_add_reinforcement(
                    self.get_pair_min_reinforcements()['defender'],
                    u_defender  
                )
        #left only defenders
        elif u_defender is None:
            #pair the attacker with a defender reinforcement, if possible
            max_pair = self.get_pair_max_reinforcements()
            if max_pair :
                self.pair_units(u_attacker, max_pair['defender'].pop())
            #attacker added as reinforcement
            else:
                self.pair_side_add_reinforcement(
                    self.get_pair_min_reinforcements()['attacker'],
                    u_attacker
                )
            
        #pair the attacker and the defender
        else:
            self.pairs.append({'attacker':[u_attacker], 'defender':[u_defender]})
        return True

    def pair_side_add_reinforcement(self, pair_side, unit):
        """
        add reinforcements to one side of a pair
        #updates pair_number_min_fighters
        """
        pair_side.append(unit)
        #FIXME
        #pair_len = len(pair_side)
        #if pair_len > self.pair_number_min_fighters:
        #        self.pair_number_min_fighters = pair_len

    def update_pairs(self):
        """
        reassign the fighters who don't have opponents
        returns False if can't update : one of the two side has no more units, True otherwise
        """
        
        #check if there is still two side
        if self.units_attacker == [] or self.units_defender == []:
            return False
        
        #we get the units without opponents
        defenders_to_reassign = []
        attackers_to_reassign = []
        new_pairs = []
        for pair in self.pairs:
            if len(pair['attacker']) == 0:
                defenders_to_reassign += pair['defender']
            elif len(pair['defender']) == 0:
                attackers_to_reassign += pair['attacker']
            else:
                new_pairs.append(pair)
                
        self.pairs = new_pairs
                
        #create new pairs
        #for pair in self.pairs:
        #    if pair['attacker'] == []:
        #        print '++++++++++++ ATTACKER EMPTY dans update_pairs'
        #    if pair['defender'] == []:
        #        print '++++++++++++ DEFENDER EMPTY dans update_pairs'
        self.build_pairs(attackers_to_reassign, defenders_to_reassign)
        
        return True

    def get_pair_min_reinforcements(self):
        "return one of the pair with the least reinforcements"
        if len(self.pairs) == 0:
            raise Exception
        while True:
            for pair in self.pairs:
                #we are looking for a pair for which the side where there is
                #more than one people is <= pair_number_min_fighters
                if len(pair['attacker']) <= self.pair_number_min_fighters \
                        and len(pair['defender']) <= self.pair_number_min_fighters:
                    return pair
            #we haven't found anybody: one of the side 
            #have many more units than the other
            #every pair has the same number on this side,
            #we increase the max reinforcement number
            self.pair_number_min_fighters += 1
            #new number: try again!

    def get_pair_max_reinforcements(self):
        """"
        return one of the pair with the max reinforcements, if exists
        if no pair has any reinforcements, returns False
        """
        for pair in self.pairs:
            #we are looking for a pair for which a side has the max reinforcements
            #e.g. min+1
            if pair['attacker'] == self.pair_number_min_fighters+1 \
                    or pair['defender'] == self.pair_number_min_fighters+1:
                return pair
        
        if self.pair_number_min_fighters == 1:
            return False
        
        #no pair has that much reinforcement, we decrease the min reinforcement number
        self.pair_number_min_fighters -= 1
        #new number: try again!
        self.get_pair_max_reinforcements()

    def fight(self):
        """ Process all the rounds of the fight """
        while self.units_defender != [] and self.units_attacker != [] \
                and self.current_round <= ROUND_MAX:
            self.fight_a_round()
            #if can't update pairs, there is a winner
            if not self.update_pairs():
                break
    
    def fight_a_round(self):
        """ Process a round of fight """
        for pair in self.pairs:
            self.fight_in_pair(pair)
            self.clean_pair(pair)
        #for pair in self.pairs:
        #    if pair['attacker'] == []:
        #        print '=================== ATTACKER EMPTY ========================'
        #    if pair['defender'] == []:
        #        print '=================== DEFENDER EMPTY ========================'
        self.store_results()
       
        self.current_round += 1
        
    def fight_in_pair(self, pair):
        #print pair
        """ Process the fight of a given pair """
        try:
            for unit in pair['attacker']:
                unit.hit_unit(choice(pair['defender']))
                #ranged units attack once more
                if unit.fighting_unit_type.unit_type.is_ranged():
                    unit.hit_unit(choice(pair['defender']))
            for unit in pair['defender']:
                unit.hit_unit(choice(pair['attacker']))
                #ranged units attack once more
                if unit.fighting_unit_type.unit_type.is_ranged():
                    unit.hit_unit(choice(pair['attacker']))
        except IndexError:
            print '-------------------------------------------'
            print 'Index Error dans fight_in_pair'
            print pair

    def clean_pair(self, pair):
        """ move the dead and the wounded from the fighters """
        for unit in pair['attacker']:
            state = unit.check_state()
            if state == 'dead':
                self.units_dead_attacker.append(unit)
                pair['attacker'].remove(unit)
                self.units_attacker.remove(unit)
            elif state == 'wounded':
                self.units_fleeing_attacker.append(unit)
                pair['attacker'].remove(unit)
                self.units_attacker.remove(unit)
        for unit in pair['defender']:
            state = unit.check_state()
            if state == 'dead':
                self.units_dead_defender.append(unit)
                pair['defender'].remove(unit)
                self.units_defender.remove(unit)
            elif state == 'wounded':
                self.units_fleeing_defender.append(unit)
                pair['defender'].remove(unit)
                self.units_defender.remove(unit)

    def is_attacker_winner(self):
        """
        True/False, None if draw
        """
        if self.units_attacker != [] and self.units_defender != []:
            return None
        elif self.units_defender == []:
            return True
        else:
            return False

    def fight_result_str(self):
        """
        Returns a string about the fight result:
        - draw
        - defender wins
        - attacker wins
        """
        is_attacker_winner = self.is_attacker_winner()
        if is_attacker_winner == None:
            return 'draw'
        elif is_attacker_winner:
            return 'attacker wins'
        else:
            return 'defender wins'

    def present_results(self):
        """ nicely presents the fight results in the attack_deads,
        defense_deads, attack_fleeing and defense_fleeing dicts"""

        """
        self.attack_deads = Counter(
                [i.fighting_unit_type.unit_type
                    for i in self.units_dead_attacker
                ])

        self.defense_deads = Counter(
                [i.fighting_unit_type.unit_type
                    for i in self.units_dead_defender
                ])

        self.attack_fleeing = Counter(
                [i.fighting_unit_type.unit_type
                    for i in self.units_fleeing_attacker
                ])

        self.defense_fleeing = Counter(
                [i.fighting_unit_type.unit_type
                    for i in self.units_fleeing_defender
                ])
            #units still fighting at the end of the combat
        self.attack_remain = Counter(
                    [i.fighting_unit_type.unit_type
                        for i in self.units_attacker]
                ) + self.attack_fleeing

        self.defense_remain = Counter(
                    [i.fighting_unit_type.unit_type
                        for i in self.units_defender]
                ) + self.defense_fleeing

        self.attack_deads = dict(self.attack_deads)
        self.attack_fleeing = dict(self.attack_fleeing)
        self.attack_remain = dict(self.attack_remain)
        self.defense_deads = dict(self.defense_deads)
        self.defense_fleeing = dict(self.defense_fleeing)
        self.defense_remain = dict(self.defense_remain)
        """
        (   (self.attack_remain, self.defense_remain),
                (self.attack_deads, self.defense_deads),
                (self.attack_fleeing, self.defense_fleeing)
                ) = self.record_rounds[-1]

        self.attack_remain = dict(
                Counter(self.attack_remain)\
                        + Counter(self.attack_fleeing))
        self.defense_remain = dict(
                Counter(self.defense_remain)\
                        + Counter(self.defense_fleeing))


    def store_results(self):
        """Store the partial results at the end of a round in self.record_rounds"""
        attack_deads = Counter(
                [i.fighting_unit_type.unit_type
                    for i in self.units_dead_attacker
                ])

        defense_deads = Counter(
                [i.fighting_unit_type.unit_type
                    for i in self.units_dead_defender
                ])

        attack_fleeing = Counter(
                [i.fighting_unit_type.unit_type
                    for i in self.units_fleeing_attacker
                ])

        defense_fleeing = Counter(
                [i.fighting_unit_type.unit_type
                    for i in self.units_fleeing_defender
                ])
            #units still fighting at the end of the combat
        attack_remain = Counter(
                    [i.fighting_unit_type.unit_type
                        for i in self.units_attacker]
                )

        defense_remain = Counter(
                    [i.fighting_unit_type.unit_type
                        for i in self.units_defender]
                )

        attack_deads = dict(attack_deads)
        attack_fleeing = dict(attack_fleeing)
        attack_remain = dict(attack_remain)
        defense_deads = dict(defense_deads)
        defense_fleeing = dict(defense_fleeing)
        defense_remain = dict(defense_remain)

        item = (
                (attack_remain, defense_remain),
                (attack_deads, defense_deads),
                (attack_fleeing, defense_fleeing)
                )

        self.record_rounds.append(item)
        


    def make_report(self):
        self.report = render_to_string('game/reports/combat.html',
                {'combat': self}
                )

    def make_round_report(self):
        pass
