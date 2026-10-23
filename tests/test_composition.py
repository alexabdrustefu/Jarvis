import unittest

from composition import create_application


class FakeStore:
    def get_preferences(self):
        return {"llm_provider": "lmstudio"}


class FakeAI:
    provider_preference = "auto"


class FalseyDependency:
    def __bool__(self):
        return False


class CompositionTests(unittest.TestCase):
    def test_all_interfaces_receive_one_shared_router_and_store(self):
        store = FakeStore()
        ai = FakeAI()
        email, news, system, audio = object(), object(), object(), object()

        application = create_application(
            store=store, ai=ai, email=email, news=news, system=system, audio=audio,
        )

        self.assertIs(application.store, store)
        self.assertIs(application.router.local_commands.store, store)
        self.assertIs(application.router.ai, ai)
        self.assertIs(application.router.email, email)
        self.assertIs(application.router.news, news)
        self.assertIs(application.router.system, system)
        self.assertIs(application.router.audio, audio)
        self.assertEqual(ai.provider_preference, "lmstudio")

    def test_explicit_falsey_dependencies_are_not_replaced(self):
        store = FakeStore()
        ai = FakeAI()
        email, news = FalseyDependency(), FalseyDependency()

        application = create_application(store=store, ai=ai, email=email, news=news)

        self.assertIs(application.router.email, email)
        self.assertIs(application.router.news, news)


if __name__ == "__main__":
    unittest.main()
