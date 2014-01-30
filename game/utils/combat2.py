#!/usr/bin/python
#vim: set fileencoding=utf-8 :
from random import choice, randint, shuffle
from ..models import UnitType


ROUND_MAX = 6
SEUIL_KO = 40 #in %


class FightingUnitType:
    """ keeps the stat of a unit for a tribe"""
    name = ''
    attack = 0
    defense = 0
    HP_max = 0
    
    def __init__(self, unit_type, tribe=None, opponent_tribe=None):
        self.name = unit_type.name
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
        elif self.HP_left < self.fighting_unit_type.HP_max*SEUIL_KO/100 \
                and randint(0, SEUIL_KO) > (self.HP_left // self.fighting_unit_type.HP_max):
            return 'wounded'
        return 'OK'

class Combat2:
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
    
    #nb_attackers = 0
    #nb_defenders = 0
    #attackers = []
    #attackers_ko = []
    #nb_attackers_ko = 0
    #defenders = []
    #defenders_ko = []
    #nb_defenders_ko = 0
    #nb_attackers_survivants = 0
    #nb_defenders_survivants = 0
    
    #list of dict containing pairs of "attacker" and "defender" unit lists
    pairs = ()
    
    #list of FightingUnitType objects
    unit_types_attacker = {}
    unit_types_defender = {}
    
    #lists of FightingUnit
    units_attacker = []
    units_defender = []
    units_dead_attacker = []
    units_dead_defender = []
    units_fleeing_attacker = []
    units_fleeing_defender = []
    
    
    #number min of fighters in a combat pair on the most numerous side
    pair_number_min_fighters = 1

    current_round = 0
    rapport = ''
    
    
    def __init__(self, attackers, defenders):
        """
        attackers and defenders are Group objects
        
        In this class,
        units are FightingUnit objects
        unit types are FightingUnitType objects
        """
        
        
        unit_types = UnitType.objects.filter(name__in = \
            [u.name for u in attackers.unit_stack_set])
        
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
                opponent_tribe=defenders.get_tribe()
            ))
            #defender
            try:
                defenders_tribe = self.defenders.village.tribe
            except AttributeError:
                defenders_tribe = None                
            self.unit_types_defender[u.name] = (FightingUnitType(
                unit_type=u,
                tribe=defenders_tribe,
                opponent_tribe=attackers_tribe
            ))
            
        #creation of each unit
        for pile in self.attaquers.unitstack_set.all():
            fighting_unit_type = (self.unit_types_attacker[pile.unit_type.name])
            for i in xrange(1, pile.number):
                self.units_attacker.append(FightingUnit(fighting_unit_type))
        for pile in self.defenders.unitstack_set.all():
            fighting_unit_type = (self.unit_types_defender[pile.unit_type.name])
            for i in xrange(1, pile.number):
                self.units_defender.append(FightingUnit(fighting_unit_type))
        
        
        self.nb_attackers = len(self.units_attacker)
        self.nb_defenders = len(self.units_defender)
        
        self.build_pairs(self.units_attacker, self.units_defender)
        self.fight()
        
        
        self.rapport += ('%s; %s\n')\
                % (self.nb_attackers, self.nb_defenders)
        #self.se_battre()
        #self.nb_attackers_survivants = len(self.attackers_ko)
        #self.nb_defenders_survivants = len(self.defenders_ko)
    



    def build_pairs(self, units_attacker, units_defender):
        """ Build the pairs of fighters with the given lists of FightingUnit"""
        
        #shuffle the units
        shuffle(units_attacker)
        shuffle(units_defender)
            
        #build pairs
        for i in max(len(units_attacker), len(units_defender)):
            #get an attacker
            try:
                u_attacker=units_attacker.pop()
            except IndexError:
                u_attacker=None
            #get a defender
            try:
                u_defender=units_defender.pop()
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
        if u_attacker==None and u_defender==None:
            return False
        #left only attackers
        elif u_attacker==None:
            #pair the defender with an attacking reinforcement, if possible
            attacker_units = self.get_pair_max_reinforcements()['attacker']
            if attacker_units :
                self.pair_units(attacker_units.pop(), u_defender)
            #attacker added as reinforcement
            else:
                self.pair_side_add_reinforcement(
                    self.get_pair_min_reinforcements()['defender'],
                    u_defender
                )
        #left only defenders
        elif u_attacker==None:
            #pair the attacker with a defender reinforcement, if possible
            defender_units = self.get_pair_max_reinforcements()['defender']
            if defender_units :
                self.pair_units(u_attacker, defender_units.pop())
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
        "reassign the fighters who don't have opponents"
        
        #we get the units without opponents
        defenders_to_reassign = []
        attackers_to_reassign = []
        for pair in self.pairs:
            if len(pair['attacker']) == 0:
                defenders_to_reassign += pair['defender']
            if len(pair['defender']) == 0:
                attackers_to_reassign += pair['attacker']
                
        #create new pairs
        self.build_pairs(attackers_to_reassign, defenders_to_reassign)


    def get_pair_min_reinforcements(self):
        """" return one of the pair with the least reinforcements  """
        for pair in self.pairs:
            #we are looking for a pair for which the side where there is more
            #than one people is <= pair_number_min_fighters
            if pair['attacker'] <= self.pair_number_min_fighters \
                    and pair['defender'] <= self.pair_number_min_fighters:
                return pair
        
        #we haven't found anybody: one of the side have many more units than the other
        #every pair has the same number on this side, we increase the max reinforcement number
        self.pair_number_min_fighters += 1
        #new number: try again!
        self.get_pair_min_reinforcements(self)


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
        self.get_pair_max_reinforcements(self)
    
    
    
    
    
    def fight(self):
        """ Process all the rounds of the fight """
        while self.units_defender != [] and self.units_attacker != [] \
                and self.current_round <= ROUND_MAX:
            self.fight_a_round()
    
    def fight_a_round(self):
        """ Process a round of fight """
        for pair in self.pairs:
            self.fight_in_pair(pair)
            self.clean_pair(pair)
        self.update_pairs()
        self.current_round += 1
        
    def fight_in_pair(self, pair):
        """ Process the fight of a given pair """
        for unit in pair['attacker']:
            unit.hit_unit(choice(pair['defender']))
        for unit in pair['defender']:
            unit.hit_unit(choice(pair['attacker']))


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
        
