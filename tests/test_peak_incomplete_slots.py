import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
ENTRY = '战斗任务开始-极限峰值缺员作战'

class PeakIncompleteSlotsTest(unittest.TestCase):
    def setUp(self):
        self.interface = json.loads((ASSETS / 'interface.json').read_text())
        self.nodes = json.loads((ASSETS / 'resource/base/pipeline/public/SimulatedCombat/极限峰值缺员作战.json').read_text())

    def test_option_is_off_by_default_and_only_rewires_three_peak_groups(self):
        option = self.interface['option']['极限峰值：槽位未满仍开始作战']
        self.assertEqual(option['default_case'], 'NO')
        for case in option['cases']:
            override = case['pipeline_override']
            self.assertEqual(set(override), {f'开始作战-子群{i}-极限峰值' for i in range(1, 4)})
            entry = ENTRY if case['name'] == 'YES' else '通用战斗任务开始'
            for i in range(1, 4):
                self.assertEqual(override[f'开始作战-子群{i}-极限峰值']['next'],
                    ['[JumpBack]' + entry, f'子群{i}后返回极限峰值标签页-极限峰值'])

    def test_empty_party_is_still_deployed_and_popup_never_cancels(self):
        click = self.nodes['点击作战开始按钮-极限峰值缺员作战']
        self.assertEqual(click['next'][0], '发现可部署人形提示-极限峰值缺员作战')
        popup = self.nodes[click['next'][0]]
        self.assertNotIn('action', popup)
        self.assertEqual(popup['next'], ['确认缺员作战-极限峰值'])
        self.assertEqual(self.nodes['未部署任何人形-极限峰值缺员作战']['next'], ['选中部署位-极限峰值缺员作战'])
        self.assertEqual(self.nodes['部署人形-极限峰值缺员作战']['next'], ['点击作战开始按钮-极限峰值缺员作战'])
        self.assertNotIn('取消可部署人形提示-通用战斗', json.dumps(self.nodes, ensure_ascii=False))

    def test_option_labels_and_english_popup_overlay(self):
        for lang in ['zh', 'en']:
            labels = json.loads((ASSETS / f'interface_{lang}.json').read_text())
            for key in ['极限峰值：槽位未满仍开始作战', '极限峰值缺员作战说明']:
                self.assertIn(key, labels)
        en = json.loads((ASSETS / 'resource/resource_en/pipeline/极限峰值缺员作战.json').read_text())
        self.assertEqual(en['确认缺员作战-极限峰值']['expected'], '^Confirm$')
        self.assertIn('发现可部署人形提示-极限峰值缺员作战', en)

    def test_screenshot_warning_can_resume_without_combat_start(self):
        # Manual transcription of the user's cropped popup, not an OCR result.
        warning = '还有可部署的武装小组，是否确定开始作战？'
        detector = '发现可部署人形提示-极限峰值缺员作战'
        entry = self.nodes[ENTRY]
        self.assertTrue(any(re.search(pattern, warning) for pattern in entry['expected']))
        self.assertLess(entry['next'].index(detector),
                        entry['next'].index('已进入作战开始页面-极限峰值缺员作战'))
        popup = self.nodes[detector]
        self.assertTrue(any(re.search(pattern, warning) for pattern in popup['expected']))
        for unrelated in ['可部署人形', '是否确定退出作战？', '确认购买', '注意']:
            self.assertFalse(any(re.search(pattern, unrelated) for pattern in popup['expected']))
        confirm = self.nodes[popup['next'][0]]
        self.assertIsNotNone(re.search(confirm['expected'], '确认'))
        for unrelated in ['取消', '确定', '是否确定开始作战？', '确认购买']:
            self.assertIsNone(re.search(confirm['expected'], unrelated))
        # A cropped popup supplies no game-window coordinates. Click the OCR box.
        for node in [popup, confirm]:
            self.assertNotIn('roi', node)
            self.assertNotIn('target', node)
        self.assertEqual(confirm['action'], 'Click')
        # If the first click is not accepted, recognize the warning again.
        self.assertEqual(confirm['next'][0], detector)
        en = json.loads((ASSETS / 'resource/resource_en/pipeline/极限峰值缺员作战.json').read_text())
        self.assertTrue(set(en[detector]['expected']).issubset(en[ENTRY]['expected']))

if __name__ == '__main__':
    unittest.main()
