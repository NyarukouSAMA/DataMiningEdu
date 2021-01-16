from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.functions import mode
from models import gbModels


class Database:

    def __init__(self, dbUrl):
        engine = create_engine(dbUrl)
        gbModels.Base.metadata.create_all(bind=engine)
        self.maker = sessionmaker(bind=engine)

    def getOrCreate(self, session, model, data):
        dbModel = session.query(model).filter((hasattr(model, 'url') and model.url == data['url'])
            or (hasattr(model, 'externalId') and model.externalId == data['externalId'])).first()
        if not dbModel:
            dbModel = model(**data)
        return dbModel

    def createPost(self, data: dict):
        session = self.maker()
        tags = map(lambda tagData: self.getOrCreate(session,
                                                       gbModels.Tag,
                                                       tagData
                                                       ), data['tags'])
        author = self.getOrCreate(session, gbModels.Author, data['author'])
        post = self.getOrCreate(session, gbModels.Post, data['postData'])
        post.author = author
        post.tags.extend(tags)
        session.add(post)

        for commentData in data['commentsData']:
            author = self.getOrCreate(session, gbModels.Author, commentData['author'])
            commentData['comment.referenceObjectId'] = post.id
            comment = self.getOrCreate(session, gbModels.Comment, commentData['comment'])
            comment.author = author
            session.add(comment)

        try:
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
            