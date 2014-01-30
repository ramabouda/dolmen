#!/usr/bin/python
#vim: set fileencoding=utf-8 :
"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from models import Group, Village, Resources, Cost, Technology, Human, Tribe, UnitStack
from utils import combat
from django_dynamic_fixture import G
from annoying.functions import get_object_or_None
from utils.exceptions import CannotPay, TechnologyNeeded



class OrgaTest(TestCase):
    group1 = None
    group2 = None
    typeUnite1 = None
    typeUnite2 = None

    #def setUp(self):
    #    """
    #    Rempli la bdd de tests
    #    """
    #    for model in [Tribe, UnitStack, Group, Village]:
    #        mockup = Mockup(model, generate_fk=False)
    #        mockup.create(10)
    #    group1 = Group.objects.all()[0]
    #    group2 = Group.objects.all()[1]
    #    typeUnite1 = UnitType(name='guerrier')
    #    typeUnite2 = UnitType(name='femme')
    #    typeUnite1.save()
    #    typeUnite2.save()
        
            
    
    def test_add_unit(self):
        # TODO
        pass
    


class ResourcesTest(TestCase):
    resource1 = None
    resource2 = None
    resource3 = None
    
    def setUp(self):
        self.resource1 = Resources.objects.create(
            food=200,
            silex=100,
            wood=0,
            skin=200,
        )
        self.resource2 = Resources.objects.create(
            food=500,
            silex=200,
            wood=0,
            skin=300,
        )
        self.resource3 = Resources.objects.create(
            food=800,
            silex=300,
            wood=5,
            skin=400,
        )
        
    def test_operators(self):
        self.assertFalse(self.resource1 < self.resource2)
        self.assertTrue(self.resource1 <= self.resource2)
        self.assertTrue(self.resource2 < self.resource3)
    
    def test_can_pay(self):
        c1 = Cost(resources=self.resource1, fertility=200, divinity=100)
        c2 = Cost(resources=self.resource2, fertility=300, divinity=400)
        self.assertTrue(c2.can_pay(c1))
        self.assertFalse(c1.can_pay(c2))
    
    resource1 = None
    resource2 = None
    resource3 = None



class GroupTest(TestCase):
    g1 = None
    g2 = None
    t = None
    u = None
    
       
    
    def setUp(self):
        self.g1 = G(Group, resources=G(Resources))
        self.g1.save()
        self.g2 = G(Group, resources=G(Resources))
        self.g2.save()
        
        self.t = G(Tribe)
        self.t.save()
        
        self.u = G(Human, name="Unit test", cost=G(Cost, resources=(G(Resources))))
        self.u.save()
        self.u2 = G(Human, name="Unit test 2", cost=G(Cost, resources=(G(Resources))))
        self.u2.save()
        self.u3 = G(Human, name="Unit test 3", cost=G(Cost, resources=(G(Resources))))
        self.u3.save()
        self.u4 = G(Human, name="Unit test 4", cost=G(Cost, resources=(G(Resources))))
        self.u4.save()
        
    def test_add_unit(self):
        self.g1.add_unit([(self.u, 12)])        
        self.assertTrue(get_object_or_None(
                UnitStack,
                group=self.g1,
                unit_type=self.u
            ).number == 12)
        
        
    def test_merge(self):
        self.g1.add_unit([(self.u, 12)])
        self.g1.add_unit([(self.u2, 1)])
        self.g1.add_unit([(self.u3, 2)])
        
        self.g2.add_unit([(self.u, 100)])
        self.g2.add_unit([(self.u2, 5)])
        self.g2.add_unit([(self.u4, 5)])
        
        self.g1.merge(self.g2)
        
        self.assertTrue(get_object_or_None(
                UnitStack,
                group=self.g1,
                unit_type=self.u
            ).number == 112)
        
        self.assertTrue(get_object_or_None(
                UnitStack,
                group=self.g1,
                unit_type=self.u2
            ).number == 6)
                
        self.assertTrue(get_object_or_None(
                UnitStack,
                group=self.g1,
                unit_type=self.u3
            ).number == 2)
        
        self.assertTrue(get_object_or_None(
                UnitStack,
                group=self.g1,
                unit_type=self.u4
            ).number == 5)
        
        
        
class VillageTest(TestCase):
    v1 = None
    v2 = None
    u = None
    
    def setUp(self):
        self.v1 = G(Village)
        self.v1.save()
        self.v2 = G(Village)
        self.v2.save()
        
        self.u = G(Human, name="Unit test", cost=G(Cost, resources=(G(Resources, wood=10))))
        self.u.save()
        
    def test_functions(self):
        #can pay 0 resources
        self.assertTrue(self.v1.can_pay(G(Cost, resources=(G(Resources)))))
        #can't pay that much
        self.assertRaises(CannotPay, self.v1.add_unit_creation, self.u, 1000)

    def test_pay(self):
        # pay 100 wood
        self.v1.resources.wood = 200
        self.v1.pay(G(Cost, resources=G(Resources, wood=100)))
        self.assertTrue(self.v1.resources.wood == 100)
        
        
    def test_resources_functions(self):
        self.v1.get_income()
        self.v1.update_income()
        self.v1.get_fertility_increase()
        
        r = Resources(wood=4000,food=4000,silex=4000,skin=4000)
        self.v1.receive_resources(r)
        self.assertTrue(self.v1.resources == r-self.v1.max_resources_storage())
        
        
    def test_starvation(self):
        self.v1.inhabitants.village = self.v1
        self.v1.inhabitants.add_unit([(self.u, 100)])
        self.v1.inhabitants.save()
        #self.v1.kill_one_guy()
        
        
        
        
        
class CombatTest(TestCase):
    g1 = None
    g2 = None
    t = None
    u = None
    
    
    def setUp(self):
        self.g1 = G(Group, resources=G(Resources))
        self.g1.save()
        self.g2 = G(Group, resources=G(Resources))
        self.g2.save()
        
        self.t = G(Tribe)
        self.t.save()
        
        self.u = G(Human, name="Unit-test", cost=G(Cost, resources=(G(Resources))))
        self.u.save()
        self.u2 = G(Human, name="Unit-test-2", attaque=200, cost=G(Cost, resources=(G(Resources))))
        self.u2.save()
        self.u3 = G(Human, name="Unit-test-3", cost=G(Cost, resources=(G(Resources))))
        self.u3.save()
        self.u4 = G(Human, name="Unit-test-4", defense=200, cost=G(Cost, resources=(G(Resources))))
        self.u4.save()
        
        self.g1.add_unit([(self.u, 50), (self.u3, 50)])
        self.g2.add_unit([(self.u2, 50), (self.u4, 50)])
        
    def test_combat(self):
        c = combat.Combat(self.g1, self.g2)
        #print c.fight_result_str()
        #print str(len(c.units_dead_attacker)) +' attacker units dead'
        #print str(len(c.units_dead_defender)) +' defender units dead'
        #print str(len(c.units_fleeing_attacker)) +' attacker units fleeing'
        #print str(len(c.units_fleeing_defender)) +' defender units fleeing'
        #print str(len(c.units_defender)) +' defender units left'
        #print str(len(c.units_attacker)) +' attacker units left'
        
        
        
        
        
    
class TribeTest(TestCase):
    t = None
    
    
    def setUp(self):
        self.t = G(Tribe)
        self.t.save()
        
    def test_increase_tech(self):
        tech = G(Technology, identifier="tech_test", cost=G(Cost, resources=(G(Resources))))
        self.t.increase_tech_level(tech)
        self.assertTrue(self.t.get_techno_level_by_name("tech_test") == 1)
        self.t.increase_tech_level(tech)
        self.assertTrue(self.t.get_techno_level_by_name("tech_test") == 2)
    
    def test_divinity(self):
        tech = G(Technology, identifier="pictorial_art", cost=G(Cost, resources=(G(Resources))))
        self.assertTrue(self.t.update_divinity_income() == 0)
        
        self.t.increase_tech_level(tech)
        self.assertTrue(self.t.update_divinity_income() == 1*10./24)
        
    
    
    
