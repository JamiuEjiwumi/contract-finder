import unittest
from finder import classify, canonical
class Filters(unittest.TestCase):
    def test_match(self):
        self.assertEqual(classify('DevOps engineer', 'Part-time remote contract outside IR35')[0], 'candidate')
    def test_full_time(self):
        self.assertEqual(classify('DevOps engineer', 'Full-time remote outside IR35; flexible hours')[0], 'excluded')
    def test_hybrid(self):
        self.assertEqual(classify('Platform engineer', 'Part-time outside IR35 hybrid remote')[0], 'excluded')
    def test_missing_ir35(self):
        self.assertEqual(classify('DevOps', 'part-time remote contract')[0], 'unconfirmed')
    def test_conflicting_ir35(self):
        self.assertEqual(classify('DevOps', 'part-time remote inside IR35 outside IR35')[0], 'excluded')
    def test_flexible_not_parttime(self):
        self.assertEqual(classify('DevOps', 'flexible remote outside IR35')[0], 'unconfirmed')
    def test_tracking(self):
        self.assertEqual(canonical('https://example.com/job?id=2&utm_source=x'), 'https://example.com/job?id=2')
    def test_unsafe_url(self):
        self.assertIsNone(canonical('javascript:alert(1)'))
