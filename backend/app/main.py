import os, hashlib, hmac, secrets, datetime as dt
from contextlib import asynccontextmanager
import jwt
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import select, func, or_
from .db import Base, engine, SessionLocal, User, Article, Bookmark, seed
from .ai import compare

SECRET = os.getenv("JWT_SECRET") or secrets.token_hex(32)  # ephemeral if unset: set JWT_SECRET in production
PAGE = 20


@asynccontextmanager
async def lifespan(_):
    Base.metadata.create_all(engine)  # dev convenience; Alembic migrations are not included yet
    seed()
    yield


app = FastAPI(title="PrepLens API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
                   allow_methods=["*"], allow_headers=["*"])


def db():
    with SessionLocal() as s:
        yield s


def hash_pw(p: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    return f"{salt}${hashlib.pbkdf2_hmac('sha256', p.encode(), salt.encode(), 310_000).hex()}"


def check_pw(p: str, stored: str) -> bool:
    return hmac.compare_digest(hash_pw(p, stored.split("$")[0]), stored)


def token(u: User) -> str:
    exp = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=7)
    return jwt.encode({"sub": str(u.id), "role": u.role, "exp": exp}, SECRET, "HS256")


def current_user(cred=Depends(HTTPBearer(auto_error=False)), s=Depends(db)) -> User:
    if not cred:
        raise HTTPException(401, "Please sign in.")
    try:
        u = s.get(User, int(jwt.decode(cred.credentials, SECRET, algorithms=["HS256"])["sub"]))
    except Exception:
        u = None
    if not u:
        raise HTTPException(401, "Your session has expired. Please sign in again.")
    return u


def require_admin(u: User = Depends(current_user)) -> User:
    if u.role != "ADMIN":
        raise HTTPException(403, "Administrator access required.")
    return u


class Cred(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=255)
    password: str = Field(min_length=8, max_length=128)


@app.post("/api/auth/register", status_code=201)
def register(c: Cred, s=Depends(db)):
    email = c.email.lower()
    if s.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "An account with this email already exists.")
    role = "ADMIN" if email == (os.getenv("ADMIN_EMAIL") or "").lower() else "USER"
    u = User(email=email, password_hash=hash_pw(c.password), role=role)
    s.add(u)
    s.commit()
    return {"token": token(u), "role": u.role}


@app.post("/api/auth/login")
def login(c: Cred, s=Depends(db)):
    u = s.scalar(select(User).where(User.email == c.email.lower()))
    if not u or not check_pw(c.password, u.password_hash):
        raise HTTPException(401, "Email or password is incorrect.")
    return {"token": token(u), "role": u.role}


def out(a: Article, saved: set[int]) -> dict:
    return {"id": a.id, "title": a.title, "author": a.author, "publisher": a.publisher, "published": a.published.isoformat(),
            "kind": a.kind, "exam": a.exam, "topic": a.topic, "keywords": a.keywords, "perspective": a.perspective,
            "summary": a.summary, "url": a.url, "is_demo": a.is_demo, "bookmarked": a.id in saved}


def saved_ids(s, u) -> set[int]:
    return set(s.scalars(select(Bookmark.article_id).where(Bookmark.user_id == u.id)))


@app.get("/api/articles")
def articles(q: str = Query("", max_length=200), kind: str = "", publisher: str = "", exam: str = "",
             days: int | None = Query(None, ge=1, le=3650), sort: str = Query("newest", pattern="^(newest|oldest)$"),
             page: int = Query(1, ge=1, le=1000), u=Depends(current_user), s=Depends(db)):
    stmt = select(Article)
    for term in q.split()[:8]:  # keyword search; semantic (pgvector) search is not implemented yet
        like = f"%{term}%"
        stmt = stmt.where(or_(Article.title.ilike(like), Article.summary.ilike(like),
                              Article.keywords.ilike(like), Article.topic.ilike(like)))
    for col, val in ((Article.kind, kind), (Article.publisher, publisher), (Article.exam, exam)):
        if val:
            stmt = stmt.where(col == val)
    if days:
        stmt = stmt.where(Article.published >= dt.date.today() - dt.timedelta(days=days))
    total = s.scalar(select(func.count()).select_from(stmt.subquery()))
    order = Article.published.desc() if sort == "newest" else Article.published.asc()
    rows = s.scalars(stmt.order_by(order, Article.id).offset((page - 1) * PAGE).limit(PAGE)).all()
    saved = saved_ids(s, u)
    return {"items": [out(a, saved) for a in rows], "total": total, "page": page, "page_size": PAGE,
            "publishers": sorted(s.scalars(select(Article.publisher).distinct()).all())}


@app.get("/api/bookmarks")
def bookmarks(u=Depends(current_user), s=Depends(db)):
    rows = s.scalars(select(Article).join(Bookmark, Bookmark.article_id == Article.id)
                     .where(Bookmark.user_id == u.id).order_by(Bookmark.id.desc())).all()
    return [out(a, {a.id for a in rows}) for a in rows]


@app.put("/api/bookmarks/{aid}", status_code=204)
def add_bookmark(aid: int, u=Depends(current_user), s=Depends(db)):
    if not s.get(Article, aid):
        raise HTTPException(404, "Article not found.")
    if aid not in saved_ids(s, u):
        s.add(Bookmark(user_id=u.id, article_id=aid))
        s.commit()


@app.delete("/api/bookmarks/{aid}", status_code=204)
def del_bookmark(aid: int, u=Depends(current_user), s=Depends(db)):
    for b in s.scalars(select(Bookmark).where(Bookmark.user_id == u.id, Bookmark.article_id == aid)):
        s.delete(b)
    s.commit()


@app.get("/api/topics")
def topics(u=Depends(current_user), s=Depends(db)):
    rows = s.execute(select(Article.topic, func.count()).group_by(Article.topic).order_by(Article.topic)).all()
    return [{"topic": t, "count": n} for t, n in rows]


@app.get("/api/compare")
def compare_topic(topic: str = Query(max_length=120), u=Depends(current_user), s=Depends(db)):
    arts = s.scalars(select(Article).where(Article.topic == topic).order_by(Article.id)).all()
    if len(arts) < 2:
        raise HTTPException(422, "Comparison needs at least two articles on a topic.")
    return compare(arts)


@app.get("/api/admin/stats")
def stats(_=Depends(require_admin), s=Depends(db)):
    return {"users": s.scalar(select(func.count(User.id))), "articles": s.scalar(select(func.count(Article.id))),
            "bookmarks": s.scalar(select(func.count(Bookmark.id)))}
