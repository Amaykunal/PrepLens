import os, datetime as dt
from sqlalchemy import create_engine, String, Text, Boolean, Date, ForeignKey, UniqueConstraint, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL", "sqlite:///./preplens.db"))
SessionLocal = sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(10), default="USER")


class Article(Base):
    __tablename__ = "articles"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    author: Mapped[str] = mapped_column(String(120))
    publisher: Mapped[str] = mapped_column(String(120), index=True)
    published: Mapped[dt.date] = mapped_column(Date, index=True)
    kind: Mapped[str] = mapped_column(String(20), index=True)
    exam: Mapped[str] = mapped_column(String(40))
    topic: Mapped[str] = mapped_column(String(120), index=True)
    keywords: Mapped[str] = mapped_column(String(300))
    perspective: Mapped[str] = mapped_column(String(20))
    summary: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(500))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)


class Bookmark(Base):
    __tablename__ = "bookmarks"
    __table_args__ = (UniqueConstraint("user_id", "article_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"))


# Fictional publishers and authors: this is DEMO DATA, not real news.
_D = [
    ("Reading the Border Thaw as Tactical, Not Strategic", "R. Verma", "Demo Chronicle", 2, "Editorial", "GS-II", "India-China Relations", "border security,LAC,diplomacy", "Critical",
     "Argues the recent disengagement is a tactical pause rather than a strategic reset, and that military preparedness along the LAC must continue."),
    ("Trade Dependence Outlasts the Disengagement", "S. Menon", "Sample Express", 3, "Opinion", "GS-III", "India-China Relations", "trade imbalance,supply chains,LAC", "Critical",
     "Contends that import dependence on China has grown despite border tensions and urges faster supply-chain diversification."),
    ("The Quad as a Balancing Instrument", "N. Rao", "Placeholder Mint", 5, "Analysis", "GS-II", "India-China Relations", "Quad,Indo-Pacific,diplomacy", "Analytical",
     "Maps how Quad coordination has shifted and what it signals about India balancing strategic autonomy with like-minded partners."),
    ("Semiconductor Mission Needs Fabs, Not Just Incentives", "A. Iyer", "Sample Express", 6, "Editorial", "GS-III", "Semiconductor Mission", "manufacturing,supply chains,incentives", "Mixed",
     "Welcomes the incentive scheme but argues that skilled labour, utilities and anchor customers decide whether fabrication plants succeed."),
    ("Federalism and the Cost of Simultaneous Polls", "K. Das", "Demo Chronicle", 4, "Explainer", "GS-II", "One Nation, One Election", "federalism,elections,governance", "Neutral",
     "Explains the constitutional amendments simultaneous elections would need and how they may affect the balance between Centre and states."),
    ("A Case for Simultaneous Polls", "P. Nair", "Placeholder Mint", 8, "Opinion", "GS-II", "One Nation, One Election", "elections,governance,cost", "Supportive",
     "Argues that synchronised elections would cut expenditure and policy paralysis, while conceding that federal safeguards are needed."),
]


def seed():
    with SessionLocal() as s:
        if s.scalar(select(Article.id).limit(1)):
            return
        today = dt.date.today()
        for i, (t, au, pub, ago, kind, exam, topic, kw, pers, summ) in enumerate(_D, 1):
            s.add(Article(title=t, author=au, publisher=pub, published=today - dt.timedelta(days=ago), kind=kind,
                          exam=exam, topic=topic, keywords=kw, perspective=pers, summary=summ,
                          url=f"https://example.com/demo/{i}", is_demo=True))
        s.commit()
