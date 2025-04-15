import os
import uuid
from sqlmodel import Field, SQLModel, create_engine

class ProviderKey(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    key: str = Field()
    provider_id: str = Field(index=True)
    owner_key: str = Field(index=True)
    is_active: bool = Field(default=True)
    
    def __repr__(self):
        return f"ProviderKey(id={self.id}, provider={self.provider_name}, active={self.is_active})"

if __name__=="__main__":
    db_url = os.environ.get("DATABASE_URL", "sqlite:///./test.db")
    engine = create_engine(db_url, connect_args={})
    SQLModel.metadata.create_all(engine)