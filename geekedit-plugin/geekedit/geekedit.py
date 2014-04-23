# G.E.E.K.Edit Plugin für Trac
#
# Author: David Höss
#
# Datum: 22.04.2014
#
#
#Plugin zum Erstellen, Bearbeiten und Löschen von Wikiseiten in Trac über Git
#

import re

from trac.core import *
from trac.util import *
from trac.wiki.api import IWikiChangeListener, IWikiPageManipulator
from trac.web.chrome import add_warning
from trac.versioncontrol import RepositoryManager
from trac.env import Environment
from trac.wiki.model import WikiPage

from genshi.builder import tag
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor

import os

class GeekEdit(Component):
    """Ermöglicht das lokale Verwalten von Trac Wikiseiten
    """

    implements(IWikiChangeListener, IWikiPageManipulator, INavigationContributor, IRequestHandler)


    pages = set()


    def add_wiki_file_to_trac(self):
        repos = RepositoryManager(self.env).repository_dir
        repdir = repos.split('.git')[0]
        dirList = os.listdir(repdir + 'wiki')
        dirList.sort()
        newList = []

        for sFile in dirList:
            if sFile.find('.txt') == -1:
                continue

        newList.append(sFile)

        for sFile in newList:
            filename = os.path.splitext(sFile)[0]
            content = read_file(repdir + 'wiki/' + sFile)
            page = WikiPage(self.env, filename)
            page.text = content
            page.save(author='me', comment='', remote_addr='127.0.0.1')


    def wiki_page_added(self, page):
        pass
    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        pass
    def wiki_page_deleted(self, page):
        pass
    def wiki_page_version_deleted(self, page):
        pass

    def validate(self, page):
        lines = page.text.splitlines()
        if not lines:
            return ["Page shouldn't be empty"]
        messages = []
        if not lines[0].lstrip().startswith("= "):
            messages.append("First line must be the page's '= title ='")
        # etc.
        return messages

    def prepare_wiki_page(self, req, page, fields):
        for message in self.validate(page):
            add_warning(req, message)

    def validate_wiki_page(self, req, page):
        for message in self.validate(page):
            yield ('text', message)


    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'inhaltstest'

    def get_navigation_items(self, req):
        yield ('mainnav', 'inhaltstest',
               tag.a('Inhalt testen', href=req.href.inhaltstest()))

    # IRequestHandler methods
    def match_request(self, req):
        return re.match(r'/inhaltstest(?:_trac)?(?:/.*)?$', req.path_info)

    def process_request(self, req):

        repos = RepositoryManager(self.env).repository_dir
        repdir = repos.split('.git')[0]
        dirList = os.listdir(repdir + 'wiki')
        dirList.sort()
        newList = []

        for sFile in dirList:
            if sFile.find('.txt') == -1:
                continue

        newList.append(sFile)

        for sFile in newList:
            filename = os.path.splitext(sFile)[0]
            content = read_file(repdir + 'wiki/' + sFile)
            page = WikiPage(self.env, filename)
            page.text = content.decode('unicode-escape')
            page.save(author='me', comment='', remote_addr='127.0.0.1')
            oldList.append[sFile]

            cont = content
            req.send_response(200)
            req.send_header('Content-Type', 'text/plain')
            req.send_header('Content-Length', len(cont))
            req.end_headers()
            req.write(cont)



