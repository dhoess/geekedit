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
from trac.wiki.api import IWikiChangeListener, IWikiPageManipulator, WikiSystem
from trac.web.chrome import add_warning
from trac.versioncontrol import RepositoryManager
from trac.env import Environment
from trac.wiki.model import WikiPage
from trac.versioncontrol import IRepositoryChangeListener

from genshi.builder import tag
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor

import os
import sys
import subprocess

import sqlite3


class GeekEdit(Component):
    """Ermöglicht das lokale Erstellen, Bearbeiten und Löschen von Wikiseiten in Trac
    """

    implements(IWikiChangeListener, IWikiPageManipulator, INavigationContributor, IRequestHandler, IRepositoryChangeListener)



    def __init__(self):



        print 'G.E.E.K.Edit deploying!...please standby...'



    def add_wiki_file_to_trac(self, filename, path):
        try:
            conn = self.env.get_db_cnx()
            c = conn.cursor()
            results = c.execute("SELECT name, version FROM wiki_local WHERE name= '%s'" % filename)
            if results.fetchone() is None:
                c.execute("INSERT INTO wiki_local VALUES ('%s', 0)" % filename)
                conn.commit()
            content = read_file(path)
            page = WikiPage(self.env, filename)
            page.text = content.decode('unicode-escape')
            vers = c.execute("SELECT version FROM wiki_local WHERE name = '%s'" % filename)
            local_version = vers.fetchone()[0]
            if local_version != page.version:
                print (filename + ': local page version does not match online version!')
                print ('Local version: ' + str(local_version) + ' <-> online version: ' + str(page.version) + '. Overwrite? (y/n)')
                saved_stdin = sys.stdin
                sys.stdin = open('/dev/tty', 'r')
                user_input = raw_input()
                if user_input == 'y':
                    page.save(author='me', comment='', remote_addr='127.0.0.1')
                    print (filename + ' created/modified as wiki page from version ' + str(local_version) + ' to version ' + str(page.version))
                    c.execute("UPDATE wiki_local SET version = '%s' WHERE name = '%s'" % (page.version, filename))
                    conn.commit()
                    conn.close()
                else:
                    print 'Page not created/modified'
            #print (filename + ': wikipage created/modified.')

            else:
                page.save(author='me', comment='', remote_addr='127.0.0.1')
                print (filename + ' created/modified as wiki page from version ' + str(local_version) + ' to version ' + str(page.version))
                c.execute("UPDATE wiki_local SET version = '%s' WHERE name = '%s'" % (page.version, filename))
                conn.commit()
                conn.close()
        except:
            print (filename + ' not modified or changed; remained untouched')



    def delete_wiki_page_in_trac(self, filename):
        page = WikiPage(self.env, filename)
        page.delete()
        conn = self.env.get_db_cnx()
        c = conn.cursor()
        c.execute("DELETE FROM wiki_local WHERE name = '%s'" % filename)
        conn.commit()
        conn.close()


    def wiki_page_added(self, page):
        repo = RepositoryManager(self.env).repository_dir
        repdir = repo.split('.git')[0]

        subprocess.call(["trac-admin", "", "wiki export", page.name, repdir + "wiki/" + "tmp.txt"])
        subprocess.call(["mv", repdir + "wiki/" + "tmp.txt", repdir + "wiki/" + page.name + ".txt"])
        os.chdir(repdir + "wiki/")

        subprocess.call(["git", "add", repdir + "wiki/" + page.name + ".txt"])
        subprocess.call(["git", "commit", "-m", page.name + ".txt added."])

        os.chdir(self.env.path)


    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        repo = RepositoryManager(self.env).repository_dir
        repdir = repo.split('.git')[0]


        subprocess.call(["trac-admin", "", "wiki export", page.name, repdir + "wiki/" + "tmp.txt"])
        subprocess.call(["mv", repdir + "wiki/" + "tmp.txt", repdir + "wiki/" + page.name + ".txt"])
        os.chdir(repdir + "wiki/")

        subprocess.call(["git", "add", repdir + "wiki/" + page.name + ".txt"])
        subprocess.call(["git", "commit", "-m", page.name + ".txt added."])

        os.chdir(self.env.path)

    def wiki_page_deleted(self, page):
        repo = RepositoryManager(self.env).repository_dir
        repdir = repo.split('.git')[0]

        os.chdir(repdir + "wiki/")

        subprocess.call(["git", "rm", repdir + "wiki/" + page.name + ".txt"])
        subprocess.call(["git", "commit", "-m", page.name + ".txt removed."])

        os.chdir(self.env.path)


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
        return 'wik_update'

    def get_navigation_items(self, req):
        yield ('mainnav', 'wik_update',
               tag.a('Wiki updaten', href=req.href.wik_update()))

    # IRequestHandler methods
    def match_request(self, req):
        return re.match(r'/wik_update(?:_trac)?(?:/.*)?$', req.path_info)

    def process_request(self, req):
        global page_version
        repos = RepositoryManager(self.env).repository_dir
        repdir = repos.split('.git')[0]
        dirList = os.listdir(repdir + 'wiki')
        dirList.sort()
        count_do = 0
        count_no = 0

        for sFile in dirList:
            if sFile.find('.txt') == -1:
                continue
            try:
                filename = os.path.splitext(sFile)[0]
                if filename not in page_version:
                    page_version[filename] = 0
                content = read_file(repdir + 'wiki/' + sFile)
                page = WikiPage(self.env, filename)
                page.text = content.decode('unicode-escape')
                if page_version[filename] != page.version:
                    print (filename + ': local page version does not match online version!')
                    print ('Local version: ' + str(page_version[filename]) + ' <-> online version: ' + str(page.version) + '. Overwrite? (y/n)')
                    user_input = raw_input()
                    if user_input == 'y':
                        page.save(author='me', comment='', remote_addr='127.0.0.1')
                        count_do = count_do + 1
                        print (filename + ' created/modified as wiki page from version ' + str(page_version[filename]) + ' to version ' + str(page.version))
                        page_version[filename] = page.version
                    else:
                        print 'Page not created/modified'
                        count_no = count_no + 1
                        continue
                else:
                    page.save(author='me', comment='', remote_addr='127.0.0.1')
                    count_do = count_do + 1
                    print (filename + ' created/modified as wiki page from version ' + str(page_version[filename]) + ' to version ' + str(page.version))
                    page_version[filename] = page.version
            except:
                count_no = count_no + 1
                print (filename + ' not modified or changed; remained untouched')
                continue

        cont = str(count_do) + ' wiki pages created/modified and ' + str(count_no) + ' untouched'
        req.send_response(200)
        req.send_header('Content-Type', 'text/plain')
        req.send_header('Content-Length', len(cont))
        req.end_headers()
        req.write(cont)

    def changeset_added(self, repos, changeset):
        newchange = changeset
        repo = RepositoryManager(self.env).repository_dir
        repdir = repo.split('.git')[0]
        changes = list(newchange.get_changes())
        print '....handling wikipages.......'
        for change in changes:
            directory = change[0].split('/')[0]
            filename = change[0].split('/')[1]
            pagename = filename.split('.txt')[0]
            extension = filename.split(pagename)[1]

            if (directory == 'wiki' and extension == '.txt'):
                path = repdir + change[0]

                if change[2] == 'edit' or change[2] == 'add':
                    self.add_wiki_file_to_trac(pagename, path)

                elif change[2] == 'delete':
                    self.delete_wiki_page_in_trac(pagename)
                    print (filename + ': wikipage removed.')

                else:
                    print 'Nothing todo.'
            else:
                print 'File was no textfile. Keep going.'
            print '....wikipage handling done......have a nice day :)!'

