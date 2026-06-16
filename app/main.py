from fastapi import FastAPI, HTTPException

from app.config import settings
from app.schemas import PromptRequest, PromptResponse
from app.rag.generator import ResponseGenerator
from app.rag.prompt_builder import SYSTEM_PROMPT, build_user_prompt
from app.rag.retrieval import retrieve_context

app = FastAPI(title='Medium Article RAG Assistant')


@app.post('/api/prompt', response_model=PromptResponse)
def prompt(payload: PromptRequest) -> PromptResponse:
    try:
        contexts = retrieve_context(payload.question, top_k=settings.top_k)
        user_prompt = build_user_prompt(payload.question, contexts)

        if contexts:
            response_text = ResponseGenerator().generate(SYSTEM_PROMPT, user_prompt)
        else:
            response_text = "I don't know based on the provided Medium articles data."

        return PromptResponse(
            response=response_text,
            context=contexts,
            Augmented_prompt={'System': SYSTEM_PROMPT, 'User': user_prompt},
        )
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get('/api/stats')
def stats() -> dict:
    return {
        'chunk_size': settings.chunk_size,
        'overlap_ratio': settings.overlap_ratio,
        'top_k': settings.top_k,
    }
