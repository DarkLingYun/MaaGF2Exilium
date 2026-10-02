"""Execute real anchor/JumpBack routing; all perception and input are simulated."""
import json
from pathlib import Path
import unittest

import json5
from test_peak_runtime import run_pipeline

ROOT = Path(__file__).resolve().parents[1]
ANCHOR = '极限峰值缺员确认'
DETECTOR = '发现可部署人形提示-极限峰值'
CONFIRM = '确认缺员作战-极限峰值'


class PeakScopeTest(unittest.TestCase):
    def scenario(self, enabled=True, peak=True, empty=False, followup=False,
                 failed=False, confirm_attempts=1, group=1):
        nodes = json5.loads((ROOT / 'assets/resource/base/pipeline/public/通用战斗.json').read_text(encoding='utf-8'))
        mode = json5.loads((ROOT / 'assets/resource/base/pipeline/public/SimulatedCombat/极限峰值.json').read_text(encoding='utf-8'))
        start = f'开始作战-子群{group}-极限峰值'
        returned = f'子群{group}后返回极限峰值标签页-极限峰值'
        nodes[start] = mode[start]
        nodes[returned] = mode[returned]
        interface = json.loads((ROOT / 'assets/interface.json').read_text(encoding='utf-8'))
        case = next(c for c in interface['option']['极限峰值：槽位未满仍开始作战']['cases']
                    if c['name'] == ('YES' if enabled else 'NO'))
        for name, override in case['pipeline_override'].items():
            if name in nodes:
                nodes[name].update(override)
        # Settlement/navigation are external to the scope regression. Preserve
        # the real shared entry, deployment, warning, confirmation and anchors.
        nodes['任务完成-通用战斗']['next'] = []
        nodes['任务失败-通用战斗']['next'] = []
        nodes[returned]['next'] = ['测试普通入口'] if followup else []
        nodes['测试普通入口'] = {'next': ['[JumpBack]通用战斗任务开始', '测试结束']}
        nodes['测试结束'] = {}
        state = dict(screen='start', phase='peak' if peak else 'ordinary',
                     filled=False, confirms=0, visited=[])

        def visible(name):
            screen = state['screen']
            return {
                start: screen == 'start',
                '测试普通入口': screen in ['start', 'other-start'],
                '测试结束': screen == 'done',
                '通用战斗任务开始': screen in ['empty', 'deployed', 'warning'],
                '已进入作战开始页面-通用战斗': screen in ['empty', 'deployed'],
                '未部署任何人形-通用战斗': screen == 'empty',
                '选中部署位-通用战斗': screen == 'empty',
                '部署人形-通用战斗': screen == 'selection',
                '点击作战开始按钮-通用战斗': screen == 'deployed',
                DETECTOR: screen == 'warning',
                CONFIRM: screen == 'warning',
                '发现可部署人形提示-通用战斗': screen == 'warning',
                '取消可部署人形提示-通用战斗': screen == 'warning',
                # Auto is already on; the auto-off template never matches.
                '任务完成-通用战斗': screen == 'battle' and not failed,
                '任务失败-通用战斗': screen == 'battle' and failed,
                returned: screen == 'done',
            }.get(name, False)

        def execute(name):
            state['visited'].append((state['phase'], name))
            if name == start:
                state['screen'] = 'empty' if empty else 'deployed'
            elif name == '测试普通入口':
                state.update(screen='deployed', phase='ordinary', filled=False)
            elif name == '选中部署位-通用战斗':
                state['screen'] = 'selection'
            elif name == '部署人形-通用战斗':
                state['screen'] = 'deployed'
            elif name == '点击作战开始按钮-通用战斗':
                state['screen'] = 'battle' if state['filled'] else 'warning'
            elif name == '取消可部署人形提示-通用战斗':
                state.update(screen='empty', filled=True)
            elif name == CONFIRM:
                state['confirms'] += 1
                if state['confirms'] >= confirm_attempts:
                    state['screen'] = 'battle'
            elif name in ['任务完成-通用战斗', '任务失败-通用战斗']:
                state['screen'] = 'done'
            elif name == returned and followup:
                state['screen'] = 'other-start'

        self.assertTrue(run_pipeline(nodes, start if peak else '测试普通入口', visible, execute))
        return state

    def test_enabled_three_groups_reuse_empty_party_deployment_and_confirm(self):
        for group in range(1, 4):
            with self.subTest(group=group):
                state = self.scenario(empty=True, group=group)
                names = [name for _, name in state['visited']]
                self.assertIn('选中部署位-通用战斗', names)
                self.assertIn('部署人形-通用战斗', names)
                self.assertIn(CONFIRM, names)
                self.assertNotIn('取消可部署人形提示-通用战斗', names)
                self.assertEqual(state['screen'], 'done')

    def test_disabled_option_keeps_original_cancel_and_deploy(self):
        names = [name for _, name in self.scenario(enabled=False)['visited']]
        self.assertIn('取消可部署人形提示-通用战斗', names)
        self.assertIn('部署人形-通用战斗', names)
        self.assertNotIn(CONFIRM, names)

    def test_ordinary_battle_without_peak_anchor_keeps_original_behavior(self):
        names = [name for _, name in self.scenario(peak=False)['visited']]
        self.assertIn('取消可部署人形提示-通用战斗', names)
        self.assertNotIn(CONFIRM, names)

    def test_return_from_peak_clears_anchor_before_other_battle_in_same_task(self):
        visited = self.scenario(followup=True)['visited']
        self.assertIn(('peak', CONFIRM), visited)
        self.assertIn(('ordinary', '取消可部署人形提示-通用战斗'), visited)
        self.assertNotIn(('ordinary', CONFIRM), visited)

    def test_failure_uses_shared_settlement_and_returns_to_mode(self):
        names = [name for _, name in self.scenario(failed=True)['visited']]
        self.assertIn('任务失败-通用战斗', names)
        self.assertEqual(names[-1], '子群1后返回极限峰值标签页-极限峰值')

    def test_confirmation_retries_only_while_warning_is_visible(self):
        state = self.scenario(confirm_attempts=2)
        names = [name for _, name in state['visited']]
        self.assertEqual(names.count(CONFIRM), 2)
        self.assertEqual(names.count(DETECTOR), 2)
