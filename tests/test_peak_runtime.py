"""Native routing regressions for live-log Peak failures; perception is simulated."""
import json
from pathlib import Path
import tempfile
import time
import unittest

from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition
from maa.resource import Resource
from maa.tasker import Tasker, LoggingLevelEnum
import numpy as np
from maa.controller import CustomController


class OfflineController(CustomController):
    def connect(self):
        return True

    def request_uuid(self):
        return 'offline-peak-test'

    def screencap(self):
        return np.zeros((720, 1280, 3), dtype=np.uint8)

    def unexpected_input(self, *args):
        raise AssertionError('Offline Peak tests must never send input')

    start_app = stop_app = click = swipe = unexpected_input
    touch_down = touch_move = touch_up = unexpected_input
    click_key = input_text = key_down = key_up = unexpected_input

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / 'assets/resource/base/pipeline/public/SimulatedCombat'


class Recognition(CustomRecognition):
    def __init__(self, visible):
        super().__init__()
        self.visible = visible

    def analyze(self, context, argv):
        return (10, 10, 20, 20) if self.visible(argv.node_name) else None


class Action(CustomAction):
    def __init__(self, execute):
        super().__init__()
        self.execute = execute

    def run(self, context, argv):
        self.execute(argv.node_name)
        return True


def run_pipeline(nodes, entry, visible, execute):
    # Retain actual transitions, hit limits and timeouts; mock external nodes.
    for node in list(nodes.values()):
        for name in node.get('next', []):
            nodes.setdefault(name.removeprefix('[JumpBack]'), {})
    for node in nodes.values():
        node.update(recognition='Custom', custom_recognition='Screens',
                    action='Custom', custom_action='Actions',
                    pre_delay=0, post_delay=0, post_wait_freezes=0)
    Tasker.set_stdout_level(LoggingLevelEnum.Error)
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        (root / 'pipeline').mkdir()
        (root / 'pipeline/peak.json').write_text(json.dumps(nodes, ensure_ascii=False))
        (root / 'default_pipeline.json').write_text(json.dumps({'Default': {'timeout': 50, 'rate_limit': 1}}))
        resource = Resource()
        resource.register_custom_recognition('Screens', Recognition(visible))
        resource.register_custom_action('Actions', Action(execute))
        if not resource.post_bundle(root).wait().status.succeeded:
            raise RuntimeError('Test bundle failed loading')
        controller = OfflineController()
        if not controller.post_connection().wait().status.succeeded:
            raise RuntimeError('Offline controller failed connecting')
        tasker = Tasker()
        tasker.bind(resource, controller)
        return tasker.post_task(entry).wait().status.succeeded


class PeakRuntimeTest(unittest.TestCase):
    def test_auto_already_on_keeps_waiting_and_consumes_victory(self):
        nodes = json.loads((PIPELINE / '极限峰值缺员作战.json').read_text())
        confirm = '确认缺员作战-极限峰值'
        self.assertEqual(nodes[confirm]['timeout'], nodes['点击作战开始按钮-极限峰值缺员作战']['timeout'])
        state = {'deadline': None, 'visited': [], 'waiting_checks': 0}
        def visible(name):
            if name == confirm:
                return state['deadline'] is None
            if name == '任务完成-通用战斗':
                state['waiting_checks'] += 1
                return state['deadline'] is not None and time.monotonic() >= state['deadline']
            # Auto is already enabled, so the existing auto-off template never matches.
            return False
        def execute(name):
            state['visited'].append(name)
            if name == confirm:
                state['deadline'] = time.monotonic() + 0.3
        self.assertTrue(run_pipeline(nodes, confirm, visible, execute))
        self.assertEqual(state['visited'], [confirm, '任务完成-通用战斗'])
        self.assertGreater(state['waiting_checks'], 1)

    def reward_scenario(self, auto_popup=False, reward=True):
        nodes = json.loads((PIPELINE / 'peakValueAssessment.json').read_text())
        state = {'screen': 'entry', 'claimed': False, 'visited': []}
        def visible(name):
            screen = state['screen']
            return {
                'clickEnterPeakValueAssessmentPage': screen == 'entry',
                'peakValueAssessmentPageEnteredForFirstTime': screen == 'popup',
                '发现新周期-极限峰值（峰值推定界面）': False,
                '进入常规峰值': screen == 'extreme',
                'peakValueAssessmentPageEnteredAgain': screen == 'regular',
                '主动打开周期报酬-峰值推定': screen == 'regular',
                'claimRewards': screen == 'popup' and reward and not state['claimed'],
                'closeResultPage': screen == 'result',
                'rewardsClaimed': screen == 'popup' and state['claimed'],
                'closePeriodicReturnsPage': screen == 'popup',
                'exitPeakValueAssessment': screen == 'closed',
                'clickBackButton': screen == 'closed',
            }.get(name, False)
        def execute(name):
            state['visited'].append(name)
            if name == 'clickEnterPeakValueAssessmentPage':
                state['screen'] = 'popup' if auto_popup else 'extreme'
            elif name == '进入常规峰值':
                state['screen'] = 'regular'
            elif name == '主动打开周期报酬-峰值推定':
                state['screen'] = 'popup'
            elif name == 'claimRewards':
                state['screen'], state['claimed'] = 'result', True
            elif name == 'closeResultPage':
                state['screen'] = 'popup'
            elif name == 'closePeriodicReturnsPage':
                state['screen'] = 'closed'
        self.assertTrue(run_pipeline(nodes, 'clickEnterPeakValueAssessmentPage', visible, execute))
        return state

    def test_reward_window_is_opened_after_switching_from_extreme(self):
        state = self.reward_scenario()
        self.assertTrue(state['claimed'])
        self.assertLess(state['visited'].index('进入常规峰值'), state['visited'].index('主动打开周期报酬-峰值推定'))
        self.assertEqual(state['visited'][-1], 'clickBackButton')

    def test_no_reward_closes_manually_opened_window(self):
        state = self.reward_scenario(reward=False)
        self.assertIn('主动打开周期报酬-峰值推定', state['visited'])
        self.assertNotIn('claimRewards', state['visited'])
        self.assertEqual(state['visited'][-1], 'clickBackButton')

    def test_automatic_reward_popup_still_works(self):
        state = self.reward_scenario(auto_popup=True)
        self.assertTrue(state['claimed'])
        self.assertNotIn('主动打开周期报酬-峰值推定', state['visited'])
