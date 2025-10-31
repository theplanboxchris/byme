import hashlib
# Database Models

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel
from typing import List, Optional
import os

# Database setup
DATABASE_PATH = os.getenv("NEW_DATABASE_PATH", "./data/keywords_new.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class KeywordGroupCategoryHash(Base):
    __tablename__ = "keyword_group_category_hash"
    id = Column(Integer, primary_key=True, index=True)
    hash_value = Column(Integer, unique=True, index=True, nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    keyword_id = Column(Integer, ForeignKey("keywords.id"))


# Database Models
class Keyword(Base):
    __tablename__ = "keywords"
    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, index=True, nullable=False)
    # Relationships via join table
    group_links = relationship("KeywordGroupCategory", back_populates="keyword")

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    categories = relationship("Category", back_populates="group")
    group_links = relationship("KeywordGroupCategory", back_populates="group")

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"))
    group = relationship("Group", back_populates="categories")
    group_links = relationship("KeywordGroupCategory", back_populates="category")

class KeywordGroupCategory(Base):
    __tablename__ = "keyword_group_category"
    id = Column(Integer, primary_key=True, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    keyword = relationship("Keyword", back_populates="group_links")
    group = relationship("Group", back_populates="group_links")
    category = relationship("Category", back_populates="group_links")

def id_for(group, category, keyword):
    s = f"{group}:{category}:{keyword}"
    return int.from_bytes(hashlib.blake2b(s.encode(), digest_size=4).digest(), 'big')

# Pydantic Models
class KeywordBase(BaseModel):
    word: str
class KeywordCreate(KeywordBase):
    pass
class KeywordResponse(KeywordBase):
    id: int
    uuid: Optional[int] = None
    class Config:
        orm_mode = True

class GroupBase(BaseModel):
    name: str
class GroupCreate(GroupBase):
    pass
class GroupResponse(GroupBase):
    id: int
    class Config:
        orm_mode = True

class CategoryBase(BaseModel):
    name: str
    group_id: int
class CategoryCreate(CategoryBase):
    pass
class CategoryResponse(CategoryBase):
    id: int
    class Config:
        orm_mode = True

class KeywordGroupCategoryCreate(BaseModel):
    keyword_id: int
    group_id: int
    category_id: int
class KeywordGroupCategoryResponse(KeywordGroupCategoryCreate):
    id: int
    class Config:
        orm_mode = True

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(title="Group/Category/Keyword API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "Group/Category/Keyword API", "version": "1.0.0"}

# Group Endpoints
@app.post("/groups", response_model=GroupResponse)
def create_group(group: GroupCreate, db: Session = Depends(get_db)):
    # Check for uniqueness
    existing = db.query(Group).filter(Group.name == group.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Group already exists.")
    db_group = Group(name=group.name)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

@app.get("/groups", response_model=List[GroupResponse])
def list_groups(db: Session = Depends(get_db)):
    return db.query(Group).all()

# Delete group endpoint
@app.delete("/groups/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found.")
    # Optionally: check for related categories/keywords and handle them
    db.delete(group)
    db.commit()
    return {"detail": "Group deleted."}

# Category Endpoints
@app.post("/categories", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    db_category = Category(name=category.name, group_id=category.group_id)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@app.get("/categories", response_model=List[CategoryResponse])
def list_categories(group_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    query = db.query(Category)
    if group_id:
        query = query.filter(Category.group_id == group_id)
    return query.all()

# Keyword Endpoints
@app.post("/keywords", response_model=KeywordResponse)
def create_keyword(keyword: KeywordCreate, db: Session = Depends(get_db)):
    db_keyword = Keyword(word=keyword.word)
    db.add(db_keyword)
    db.commit()
    db.refresh(db_keyword)
    return db_keyword

@app.get("/keywords", response_model=List[KeywordResponse])
def list_keywords(db: Session = Depends(get_db)):
    keywords = db.query(Keyword).all()
    results = []
    for kw in keywords:
        # Find the hash for this keyword (if any)
        hash_entry = db.query(KeywordGroupCategoryHash).filter_by(keyword_id=kw.id).first()
        uuid = hash_entry.hash_value if hash_entry else None
        results.append(KeywordResponse(id=kw.id, word=kw.word, uuid=uuid))
    return results

# Keyword-Group-Category Endpoints
@app.post("/keyword-group-category", response_model=KeywordGroupCategoryResponse)
def link_keyword_group_category(link: KeywordGroupCategoryCreate, db: Session = Depends(get_db)):
    db_link = KeywordGroupCategory(**link.dict())
    db.add(db_link)
    db.commit()
    db.refresh(db_link)

    # Get group, category, keyword values
    group = db.query(Group).filter(Group.id == link.group_id).first()
    category = db.query(Category).filter(Category.id == link.category_id).first()
    keyword = db.query(Keyword).filter(Keyword.id == link.keyword_id).first()
    if group and category and keyword:
        hash_value = id_for(group.name, category.name, keyword.word)
        db_hash = KeywordGroupCategoryHash(hash_value=hash_value, group_id=group.id, category_id=category.id, keyword_id=keyword.id)
        db.add(db_hash)
        db.commit()
    return db_link

@app.get("/keyword-group-category", response_model=List[KeywordGroupCategoryResponse])
def list_keyword_group_category(db: Session = Depends(get_db)):
    return db.query(KeywordGroupCategory).all()

# Filter keywords by group and category
@app.get("/groups/{group_id}/categories/{category_id}/keywords", response_model=List[KeywordResponse])
def keywords_by_group_category(group_id: int, category_id: int, db: Session = Depends(get_db)):
    links = db.query(KeywordGroupCategory).filter_by(group_id=group_id, category_id=category_id).all()
    keyword_ids = [link.keyword_id for link in links]
    keywords = db.query(Keyword).filter(Keyword.id.in_(keyword_ids)).all()
    results = []
    for kw in keywords:
        # Find the hash for this keyword in this group/category
        hash_entry = db.query(KeywordGroupCategoryHash).filter_by(
            keyword_id=kw.id, group_id=group_id, category_id=category_id
        ).first()
        uuid = hash_entry.hash_value if hash_entry else None
        results.append(KeywordResponse(id=kw.id, word=kw.word, uuid=uuid))
    return results
