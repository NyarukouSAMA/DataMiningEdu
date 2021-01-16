import requests
import bs4
from urllib.parse import urljoin
from datetime import datetime

from parsers.baseParser import BaseParser


class GbParse(BaseParser):
    __params = {
        'commentable_type': 'Post',
    }

    def __init__(self, startUrl, apiUrl, database):
        super().__init__(startUrl)
        self.apiUrl = apiUrl
        self.doneUrls = set()
        self.tasks = [self.parseTask(self.startUrl, self.pagParse)]
        self.doneUrls.add(self.startUrl)
        self.database = database
        self.userUrlStaticPart = None

    def parseTask(self, url, callback):
        def wrap():
            soup = self.__getSoup(url)
            return callback(url, soup)

        return wrap

    def run(self):
        for task in self.tasks:
            result = task()
            if result:
                self.database.createPost(result)

    def postParse(self, url, soup: bs4.BeautifulSoup) -> dict:
        commentTag = soup.find('comments', attrs={'commentable-type': 'Post'})
        commentableId = commentTag.get('commentable-id') if commentTag else None
        comments = None
        if commentableId:
            self.__params['commentable_id'] = int(commentableId)
            response = self.__get(self.apiUrl, self.__params, headers=self.__headers)
            comments = self.__getComments(response.json(), commentableId)


        postContent = soup.find('div', attrs={'class': 'blogpost-content'})
        authorNameTag = soup.find('div', attrs={'itemprop': 'author'})
        authorHref = urljoin(url, authorNameTag.parent.get('href'))

        if self.userUrlStaticPart is None:
            self.userUrlStaticPart = authorHref[:authorHref.rfind('/') + 1]
        
        postDateTime = soup.find('div', attrs={'class': 'blogpost-date-views'})
        postFirstImg = next(postContent.find_all('img'), None).get('src') if postContent is not None else None
        if postDateTime is not None:
            postDateTime = postDateTime.find('time').get('datetime') if postDateTime.find('time') is not None else None
        data = {
            'postData': {
                'url': url,
                'externalId': commentableId,
                'title': soup.find('h1', attrs={'class': 'blogpost-title'}).text,
                'imgUrl': postFirstImg,
                'createdOn': datetime.fromisoformat(postDateTime) if postDateTime is not None else None
            },
            'author': {
                'url': authorHref,
                'externalId': authorHref[authorHref.rfind('/') + 1:],
                'name': authorNameTag.text,
            },
            'tags': [{
                'name': tag.text,
                'url': urljoin(url, tag.get('href')),
            } for tag in soup.find_all('a', attrs={'class': 'small'})],
            'commentsData': comments
        }
        return data

    def pagParse(self, url, soup: bs4.BeautifulSoup):
        gbPagination = soup.find('ul', attrs={'class': 'gb__pagination'})
        aTags = gbPagination.find_all('a')
        for a in aTags:
            pagUrl = urljoin(url, a.get('href'))
            if pagUrl not in self.doneUrls:
                task = self.parseTask(pagUrl, self.pagParse)
                self.tasks.append(task)
                self.doneUrls.add(pagUrl)

        postsUrls = soup.find_all('a', attrs={'class': 'post-item__title'})
        for postUrl in postsUrls:
            postHref = urljoin(url, postUrl.get('href'))
            if postHref not in self.doneUrls:
                task = self.parseTask(postHref, self.postParse)
                self.tasks.append(task)
                self.doneUrls.add(postHref)

    def __getComments(self, commentsJson, commentableId, commentsData = []):
        for arrayElement in commentsJson:
            commentJson = arrayElement['comment']
            commentData = {
                'comment': {
                    'text': commentJson['body'],
                    'externalId': commentJson['id'],
                    'referenceExternalObjectId': commentableId,
                    'referenceObjectType': self.__params['commentable_type'],
                    'parentCommentId': commentJson['parent_id']
                },
                'author': {
                    'url': self.userUrlStaticPart + commentJson['user.id'],
                    'externalId': commentJson['user.id'],
                    'name': commentJson['user.full_name']
                }
            }
            commentsData.append(commentData)
            if len(commentJson['children']) > 0:
                self.__getComments(commentJson['children'], commentableId, commentsData)
        
        return commentsData


        