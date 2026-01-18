import unittest
import time
from backend.tracker import Tracker
from backend.game import GameState

class TestGameLogic(unittest.TestCase):
    def test_tracker_grace_period(self):
        tracker = Tracker()
        
        # 1. Update with target
        dets = [{'text': 'ALPHA', 'bbox': [[300, 220], [340, 220], [340, 260], [300, 260]]}] # Centerish
        tracker.update(dets)
        
        active = tracker.get_active_targets()
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]['id'], 'ALPHA')
        
        # 2. Wait a bit (less than grace)
        time.sleep(0.1)
        active = tracker.get_active_targets()
        self.assertEqual(len(active), 1)
        
        # 3. Wait more (exceed grace 0.5s)
        time.sleep(0.6)
        active = tracker.get_active_targets()
        self.assertEqual(len(active), 0)
        
    def test_targeting_and_damage(self):
        game = GameState()
        game.init_game("Tester", "casual", "vanguard")
        
        # 1. Add target to tracker (ALPHA is usually enemy 0)
        # Center of 640x480 is 320, 240
        # Bbox around center
        dets = [{'text': 'ALPHA', 'bbox': [[300, 220], [340, 220], [340, 260], [300, 260]]}]
        game.tracker.update(dets)
        
        # 2. Attempt shot
        initial_hp = game.enemies[0]['hp']
        result = game.attempt_shot()
        
        self.assertTrue(result['fired'])
        self.assertIn('ALPHA', result['hits'])
        self.assertLess(game.enemies[0]['hp'], initial_hp)
        
    def test_miss_off_center(self):
        game = GameState()
        game.init_game("Tester", "casual", "vanguard")
        
        # Target far away (0,0)
        dets = [{'text': 'ALPHA', 'bbox': [[0, 0], [10, 0], [10, 10], [0, 10]]}]
        game.tracker.update(dets)
        
        initial_hp = game.enemies[0]['hp']
        result = game.attempt_shot()
        
        self.assertTrue(result['fired'])
        self.assertEqual(len(result['hits']), 0)
        self.assertEqual(game.enemies[0]['hp'], initial_hp)

    def test_enemy_mapping(self):
        game = GameState()
        game.init_game("Tester", "casual", "vanguard")
        
        # Target "enemy_1" -> Should map to ALPHA (index 0)
        dets = [{'text': 'enemy_1', 'bbox': [[300, 220], [340, 220], [340, 260], [300, 260]]}]
        game.tracker.update(dets)
        
        initial_hp = game.enemies[0]['hp']
        result = game.attempt_shot()
        
        self.assertTrue(result['fired'])
        self.assertIn('ALPHA', result['hits']) # Should return the ID "ALPHA"
        self.assertLess(game.enemies[0]['hp'], initial_hp)

if __name__ == '__main__':
    unittest.main()
