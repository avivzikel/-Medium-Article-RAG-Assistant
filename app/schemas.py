from pydantic import BaseModel, Field


class PromptRequest(BaseModel):
    question: str = Field(..., min_length=1)


class ContextItem(BaseModel):
    article_id: str
    title: str
    chunk: str
    score: float


class AugmentedPrompt(BaseModel):
    System: str
    User: str


class PromptResponse(BaseModel):
    response: str
    context: list[ContextItem]
    Augmented_prompt: AugmentedPrompt
