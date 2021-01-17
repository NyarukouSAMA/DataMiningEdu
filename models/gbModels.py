from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import DateTime

Base = declarative_base()

"""
one-to-one
one-to-many - many-to-one
many-to-many
"""

#It's very interesting feature, but in ms sql for unique string column u should indicate length of the string
class MixIdUrl:
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(2048), nullable=False, unique=True) 


tagPost = Table(
    'tagPost',
    Base.metadata,
    Column('postId', Integer, ForeignKey('post.id')),
    Column('tagId', Integer, ForeignKey('tag.id'))
)


class Post(Base, MixIdUrl):
    __tablename__ = 'post'
    externalId = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    imgUrl = Column(String)
    createdOn = Column(DateTime, nullable=False)
    authorId = Column(Integer, ForeignKey('author.id'))
    author = relationship('Author')
    tags = relationship('Tag', secondary=tagPost)

class Author(Base, MixIdUrl):
    __tablename__ = 'author'
    externalId = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    posts = relationship('Post')
    comments = relationship('Comment')

class Tag(Base, MixIdUrl):
    __tablename__ = 'tag'
    name = Column(String, nullable=False)
    posts = relationship('Post', secondary=tagPost)

class Comment(Base):
    __tablename__ = 'comment'
    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String, nullable=False)
    authorId = Column(Integer, ForeignKey('author.id'))
    externalId = Column(Integer, nullable=False, unique=True)
    referenceObjectId = Column(Integer, nullable=False)
    referenceExternalObjectId = Column(Integer, nullable=False)
    referenceObjectType = Column(String, nullable=False)
    parentCommentId = Column(Integer, nullable=True)
    author = relationship('Author')