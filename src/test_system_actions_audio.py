import unittest

from actions.system_actions_audio import SystemActions, is_volume_command


class FakeVolumeInterface:
    def __init__(self, scalar: float):
        self.scalar = scalar

    def GetMasterVolumeLevelScalar(self) -> float:
        return self.scalar

    def SetMasterVolumeLevelScalar(self, scalar: float, context: object) -> None:
        assert context is None
        self.scalar = scalar


class SystemActionsAudioTests(unittest.TestCase):
    def create_actions(self, current_volume: int) -> tuple[SystemActions, FakeVolumeInterface]:
        actions = SystemActions.__new__(SystemActions)
        interface = FakeVolumeInterface(current_volume / 100)
        actions.volume_interface = interface
        return actions, interface

    def test_increases_volume_and_clamps_at_maximum(self) -> None:
        actions, interface = self.create_actions(95)

        response = actions.adjust_volume("alza il volume di 10")

        self.assertEqual(response, "Fatto, Volume aumentato al 100 percento.")
        self.assertEqual(interface.scalar, 1.0)

    def test_decreases_volume_and_clamps_at_zero(self) -> None:
        actions, interface = self.create_actions(5)

        response = actions.adjust_volume("abbassa il volume di 10")

        self.assertEqual(response, "Fatto, Volume abbassato al 0 percento.")
        self.assertEqual(interface.scalar, 0.0)

    def test_sets_explicit_volume(self) -> None:
        actions, interface = self.create_actions(30)

        response = actions.adjust_volume("imposta il volume al 65")

        self.assertEqual(response, "Volume impostato al 65 percento.")
        self.assertEqual(interface.scalar, 0.65)

    def test_explicit_volume_is_clamped(self) -> None:
        actions, interface = self.create_actions(30)

        response = actions.adjust_volume("volume a 150")

        self.assertEqual(response, "Volume impostato al 100 percento.")
        self.assertEqual(interface.scalar, 1.0)

    def test_mutes_and_sets_maximum(self) -> None:
        actions, interface = self.create_actions(30)
        self.assertEqual(actions.adjust_volume("metti muto"), "Audio disattivato.")
        self.assertEqual(interface.scalar, 0.0)

        self.assertEqual(
            actions.adjust_volume("volume al massimo"),
            "Volume impostato al massimo.",
        )
        self.assertEqual(interface.scalar, 1.0)


class VolumeCommandRoutingTests(unittest.TestCase):
    def test_routes_supported_volume_commands(self) -> None:
        for command in (
            "alza il volume",
            "abbassa il volume di 10",
            "imposta il volume al 50",
            "volume a 40",
            "volume al massimo",
            "qual è il volume",
            "muta",
            "silenzio",
        ):
            with self.subTest(command=command):
                self.assertTrue(is_volume_command(command))

    def test_does_not_route_unrelated_sentences(self) -> None:
        self.assertFalse(is_volume_command("che tempo fa oggi"))
        self.assertFalse(is_volume_command("parlami della musica"))


if __name__ == "__main__":
    unittest.main()
