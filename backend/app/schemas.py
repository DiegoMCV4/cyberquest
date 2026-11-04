from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Zone = Literal["redes", "vulnerabilidades", "bd", "programacion"]


class Credentials(BaseModel):
    username: str = Field(pattern=r"^[A-Za-z0-9_]{3,20}$")
    password: str = Field(min_length=8, max_length=72)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    zone: str
    topic: str
    difficulty: int
    question_type: str
    text: str
    options: list[str]


class AnswerIn(BaseModel):
    option_index: int = Field(ge=0, le=3)


class AnswerOut(BaseModel):
    correct: bool
    correct_index: int
    explanation: str
    xp_gained: int
    total_xp: int


AssessmentKind = Literal["pre", "post"]


class AssessmentStartIn(BaseModel):
    kind: AssessmentKind
    topic: Zone


class AssessmentAnswerIn(BaseModel):
    kind: AssessmentKind
    topic: Zone
    question_id: int = Field(ge=1)
    option_index: int = Field(ge=0, le=5)


class SettingsIn(BaseModel):
    volume: int = Field(default=70, ge=0, le=100)
    difficulty: Literal["adaptativa", "facil", "normal", "dificil"] = "adaptativa"
    language: Literal["es"] = "es"


class DefeatIn(BaseModel):
    zone: Zone
    boss: bool = False
    final: bool = False


class BossStatus(BaseModel):
    zone: Zone
    name: str
    attack: str
    description: str
    defeated_enemies: int
    enemies_required: int
    boss_defeated: bool
    reward_xp: int


DefenseType = Literal["firewall", "acl", "ids", "cifrado"]


class TowerAnswerIn(BaseModel):
    question_id: int = Field(ge=1)
    option_index: int = Field(ge=0, le=3)
    defense: DefenseType


EscapeRoomName = Literal["bd", "programacion"]


class EscapeAnswerIn(BaseModel):
    room: EscapeRoomName
    challenge_id: str = Field(min_length=3, max_length=50)
    option_index: int = Field(ge=0, le=5)


class EscapeHintIn(BaseModel):
    room: EscapeRoomName
    challenge_id: str = Field(min_length=3, max_length=50)


class DetectiveAnswerIn(BaseModel):
    challenge_id: str = Field(min_length=3, max_length=50)
    option_index: int = Field(ge=0, le=5)


class FinalAnswerIn(BaseModel):
    option_index: int = Field(ge=0, le=5)


MentorTopic = Literal["redes", "seguridad", "bd", "programacion", "detective", "jefe_final"]


class MentorHintIn(BaseModel):
    topic: MentorTopic
    level: int = Field(default=1, ge=1, le=3)


class QuestionCreate(BaseModel):
    zone: Zone
    topic: str = Field(min_length=2, max_length=30)
    difficulty: int = Field(ge=1, le=3)
    question_type: str = Field(min_length=3, max_length=30)
    text: str = Field(min_length=10, max_length=2000)
    options: list[str] = Field(min_length=2, max_length=6)
    correct_index: int = Field(ge=0, le=5)
    explanation: str = Field(min_length=5, max_length=2000)
