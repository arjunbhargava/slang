import pytest

from slang.conversation import Conversation, ConversationStateError, SessionSettings
from slang.domain import LearnerLevel, Role, Transcript
from slang.fakes import FakeModelClient
from slang.languages import target_language
from slang.models.base import ModelProvider


@pytest.fixture
def conversation() -> Conversation:
    settings = SessionSettings(
        target=target_language("es", allow_unverified=True),
        level=LearnerLevel.A2,
        model_provider=ModelProvider.ANTHROPIC,
        model="fake",
    )
    return Conversation(settings, max_turns=4)


def test_learner_text_is_preserved_verbatim(conversation):
    said = "Yo tengo veinte años and I want to, um, practicar"
    conversation.commit_learner(Transcript(text=said))
    assert conversation.turns[-1].text == said


def test_empty_transcript_is_rejected(conversation):
    with pytest.raises(ConversationStateError):
        conversation.commit_learner(Transcript(text="   "))
    assert conversation.turns == ()


def test_roles_alternate(conversation):
    with pytest.raises(ConversationStateError):
        conversation.add_tutor("hola")
    conversation.commit_learner(Transcript(text="hola"))
    with pytest.raises(ConversationStateError):
        conversation.commit_learner(Transcript(text="otra vez"))


def test_failed_reply_can_be_rolled_back(conversation):
    conversation.commit_learner(Transcript(text="hola"))
    conversation.discard_pending_learner()
    assert conversation.turns == ()


def test_context_is_bounded_and_starts_with_learner(conversation):
    for index in range(5):
        conversation.commit_learner(Transcript(text=f"l{index}"))
        conversation.add_tutor(f"t{index}")
    assert [t.text for t in conversation.turns] == ["l3", "t3", "l4", "t4"]
    conversation.commit_learner(Transcript(text="l5"))
    assert conversation.turns[0].role is Role.LEARNER
    assert len(conversation.turns) <= 4


async def test_request_round_trip_with_fake_model(conversation):
    model = FakeModelClient(["¡Muy bien!"])
    conversation.commit_learner(Transcript(text="hola"))
    reply = await model.complete(conversation.request("system"))
    conversation.add_tutor(reply.text)
    assert model.requests[0].turns[-1].text == "hola"
    assert conversation.turns[-1].text == "¡Muy bien!"


def test_edit_marks_transcript():
    original = Transcript(text="yo soy veinte")
    assert original.with_edit("yo soy veinte") is original
    assert original.with_edit("yo tengo veinte").edited
