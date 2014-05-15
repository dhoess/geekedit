from trac.core import *
from trac.util import *
from trac.wiki.api import IWikiChangeListener, IWikiPageManipulator
from trac.versioncontrol.api import RepositoryManager

from git import *


printstuff = git('diff-tree', '--no-commit-id', '--name-only', '-r eb3d8e8')
print printstuff

