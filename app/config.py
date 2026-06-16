from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    chunk_size: int = 512
    overlap_ratio: float = 0.2
    top_k: int = 7

    zyrangg_api_key: str = ''
    zyrangg_base_url: str = 'https://api.zyrangg.com/v1'
    embedding_model: str = 'ZYRANGG-text-embedding-3-small'
    chat_model: str = 'ZYRANGG-gpt-5-mini'

    pinecone_api_key: str = ''
    pinecone_index_name: str = 'medium-articles-rag'
    pinecone_namespace: str = 'default'
    pinecone_cloud: str = 'aws'
    pinecone_region: str = 'us-east-1'


settings = Settings()
