#!/usr/bin/python
# -*- coding: utf-8  -*-

# This bot looks through a page, and checks for links, if a link is found it 
# searches for the link on wikibooks, if it's not found there it looks on 
# wikipedia, then finally if nothing is found there, it removes the link, this
# is fairly site specific, and then very user specific.
#
# This bot uses the pyWikipedia framework.

#
# (C) Jacob Hacker (aka Hethrir), 2011
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: rewikify.py 9359 2011-07-10 12:22:39Z xqt $'
#

import re, sys, os
sys.path.append(os.environ['HOME'] + '/dev/pywikipedia')
import wikipedia as pywikibot
import pagegenerators 
from pywikibot import i18n

from weblinkchecker import WeblinkCheckerRobot

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}


class Link:
	def __init__(self, link):
		print "Init"

class DeWikify:
    # Edit summary message that should be used is placed on /i18n subdirectory.
    # The file containing these messages should have the same name as the caller
    # script (i.e. basic.py in this case)

    def __init__(self, generator, dry, removeCites):
        """
        Constructor. Parameters:
            @param generator: The page generator that determines on which pages
                              to work.
            @type generator: generator.
            @param dry: If True, doesn't do any real changes, but only shows
                        what would have been changed.
            @type dry: boolean.
            @param removeCites: If True, remove citations as well
            @type removeCites: boolean.
        """
        self.generator = generator
        self.dry = dry
        self.removeCites = removeCites
        # Set the edit summary message
        self.summary = i18n.twtranslate(pywikibot.getSite(), 'rewikify')

    def run(self):
        for page in self.generator:
            self.treat(page)

    def treat(self, page):
	"""
	""  Finds links, checks if they exist on wikibooks, then checks if they
	""  exist on Wikipedia, if not removes the link entirely. Also remove 
	""  all "citation needed" tags.
	"""
	linksFoundInPage = []
	wikibooksPages = []
	wikipediaPages = []
	
	linksOnWikipedia = []
	redlinks = []
	
	def linkName(link):
		link = link.strip('[')
		link = link.strip(']')
		if link.find("|") != -1:
			return link[ link.find("|")+1:]
		else: return None
	def linkURL(link):
		link = link.strip('[')
		link = link.strip(']')
		if link.find("|") != -1:
			return link[ :link.find("|")]
		else: return link
	
	text = self.load(page)
	newText = text
	
	cites = []
	c = -1
	l = -1
	for i in range( len(text) ):
		"""
		"" Check for links
		"""
		if text[i] == '[' and text[i+1] == '[':
			if(text[i+2] == '#'):
				continue
			link = ""
			while text[i] != ']' and text[i-1] != ']':
				link += text[i]
				i += 1
			if linkURL(link)[:2] == "w:" or linkURL(link)[:5] == "Image" or linkURL(link)[:4] == "File":
				continue
			link += "]]"
			linksFoundInPage.append(link)
		"""
		"" Check for citations
		"""
		if self.removeCites == True:
			#print "Removing cites"
			if text[i] == '[' and text[i+1] != '[' and text[i-1] != '[':
				cite = ""
				while text[i-1] != ']':
					cite += text[i]
					i += 1
				cites.append(cite)
			if text[i] == '{' and text[i+1] == '{':
				cite = ""
				while text[i-1] != '}':
					cite += text[i]
					i += 1
				if cite == "{{Citation needed}}":
					cites.append(cite)
	
	pregen = pagegenerators.PreloadingGenerator(self.generator)
	
	# populate wikibooksPages
	for link in linksFoundInPage:
		wikibooksPages.append( pywikibot.Page( page.site(), linkURL(link) ) )
	pywikibot.getall(page.site(), wikibooksPages)
	
	# populate wikipediaPages
	wikipediaSite = pywikibot.getSite(page.site().language(), 'wikipedia')
	for link in linksFoundInPage:
		wikipediaPages.append( pywikibot.Page( wikipediaSite, linkURL(link)) )
	pywikibot.getall(wikipediaSite, wikipediaPages)
	
	# sort links, sending to linksOnWikibooks, linksOnWikipedia, or redlinks
	i = 0
	for link in linksFoundInPage:
		if wikibooksPages[i].exists():
			print "Page \"" + wikibooksPages[i].title() + "\" exists on wikibooks."
			# no need to keep a list links on wikipedia
		else:
			#check on wikipedia
			if wikipediaPages[i].exists():
				print "Page \"" + wikipediaPages[i].title() + "\" exists on wikipedia."
				linksOnWikipedia.append( linksFoundInPage[i] )
			else:
				print "Could not find page \"" + wikibooksPages[i].title() + "\" removing."
				redlinks.append( linksFoundInPage[i] )
		i += 1
	
	#
	# remove redlinks, and change wikipedia links to use w:
	#
	
	for link in linksOnWikipedia:
		if linkName(link) == None:
			print linkURL(link)
			newLink = "[[w:" + linkURL(link) + "|" + linkURL(link) + "]]"
			newText = newText.replace(link, newLink)
		else:
			newText = newText.replace(link, "[[w:" + linkURL(link) + "|" + linkName(link) + "]]" )
			print "-" + linkName(link)

	for link in redlinks:
		if linkName(link) == None:
			newText = newText.replace(link, linkURL(link))
		else:
			newText = newText.replace(link, linkName(link) )

	for cite in cites:
		newText = newText.replace(cite, '')
	
	
	text = newText
	
	"""
	""  Finished
	"""
        if not self.save(text, page, self.summary):
            pywikibot.output(u'Page %s not saved.' % page.title(asLink=True))

    def load(self, page):
        """
        Loads the given page, does some changes, and saves it.
        """
        try:
            # Load the page
            text = page.get()
        except pywikibot.NoPage:
            pywikibot.output(u"Page %s does not exist; skipping."
                             % page.title(asLink=True))
        except pywikibot.IsRedirectPage:
            pywikibot.output(u"Page %s is a redirect; skipping."
                             % page.title(asLink=True))
        else:
            return text
        return None

    def save(self, text, page, comment, minorEdit=True, botflag=True):
        # only save if something was changed
        if text != page.get():
            # Show the title of the page we're working on.
            # Highlight the title in purple.
            pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
                             % page.title())
            # show what was changed
            pywikibot.showDiff(page.get(), text)
            pywikibot.output(u'Comment: %s' %comment)
            if not self.dry:
                choice = pywikibot.inputChoice(
                    u'Do you want to accept these changes?',
                    ['Yes', 'No'], ['y', 'N'], 'N')
                if choice == 'y':
                    try:
                        # Save the page
                        page.put(text, comment=comment,
                                 minorEdit=minorEdit, botflag=botflag)
                    except pywikibot.LockedPage:
                        pywikibot.output(u"Page %s is locked; skipping."
                                         % page.title(asLink=True))
                    except pywikibot.EditConflict:
                        pywikibot.output(
                            u'Skipping %s because of edit conflict'
                            % (page.title()))
                    except pywikibot.SpamfilterError, error:
                        pywikibot.output(
u'Cannot change %s because of spam blacklist entry %s'
                            % (page.title(), error.url))
                    else:
                        return True
        return False

def main():
    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    genFactory = pagegenerators.GeneratorFactory()
    # The generator gives the pages that should be worked upon.
    gen = None
    # This temporary array is used to read the page title if one single
    # page to work on is specified by the arguments.
    pageTitleParts = []
    # If dry is True, doesn't do any real changes, but only show
    # what would have been changed.
    dry = False
    
    #Removes citations as well
    removeCites = False
    
    # Parse command line arguments
    for arg in pywikibot.handleArgs():
        if arg.startswith("-dry"):
            dry = True
        elif arg.startswith("--remove-cites"):
            removeCites = True
        else:
            # check if a standard argument like
            # -start:XYZ or -ref:Asdf was given.
            if not genFactory.handleArg(arg):
                pageTitleParts.append(arg)

    if pageTitleParts != []:
        # We will only work on a single page.
        pageTitle = ' '.join(pageTitleParts)
        page = pywikibot.Page(pywikibot.getSite(), pageTitle)
        gen = iter([page])

    if not gen:
        gen = genFactory.getCombinedGenerator()
    if gen:
        # The preloading generator is responsible for downloading multiple
        # pages from the wiki simultaneously.
        gen = pagegenerators.PreloadingGenerator(gen)
        bot = DeWikify(gen, dry, removeCites)
        bot.run()
    else:
        pywikibot.showHelp()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
