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
__version__ = '$Id: basic.py 9359 2011-07-10 12:22:39Z xqt $'
#

import wikipedia as pywikibot
import pagegenerators 
import re, sys
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
	"""
	def citeName(cite):
		cite = cite.strip('{')
		cite = cite.strip('}')
		if link.find("|") != -1:
			return link[ link.find("|")+1:]
		else: return None
	def linkURL(link):
		link = link.strip('[')
		link = link.strip(']')
		if link.find("|") != -1:
			return link[ :link.find("|")]
		else: return link
	"""	
	
	text = self.load(page)
	newText = text
	
	links = []
	cites = []
	c = -1
	l = -1
	#I would like to remove these, and have the program loop through after
	#it finds the corresponding link/cite/
	isLink = False
	isCite = False
	for i in range( len(text) ):
		"""
		"" Check for links
		"""
		if text[i] == '[' and text[i+1] == '[':
			link = ""
			while text[i] != ']' and text[i-1] != ']':
				link += text[i]
				i += 1
			if linkURL(link)[:2] == "w:" or linkURL(link)[:5] == "Image" or linkURL(link)[:4] == "File":
				continue
			links.append(link)
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
	
	print cites
	
	# Links not on wikibooks, but on wikipedia
	wikipediaLinks = []
	# Not on wikibooks or wikipedia
	redlinks = []
	
	wikipage = []
	
	for link in links:
		wikipage.append( pywikibot.Page( page.site(), linkURL(link)) )
	
	pregen = pagegenerators.PreloadingGenerator(self.generator);
	linkPages = pregen.preload(wikipage);
	
	checkWikipediaLinks = []
	
	i = 0
	for Page in linkPages:
		if Page.exists():
			print "Page \"" + Page.title() + "\" exists on wikibooks."
		else:
			print "Page \"" + Page.title() + "\" does not exist on wikibooks."
			checkWikipediaLinks.append(links[i])
		i += 1
	
	wikipediaLPages = []
	for link in checkWikipediaLinks:
		wikipediaLPages.append( pywikibot.Page( pywikibot.getSite(page.site().language(), 'wikipedia'), linkURL(link)) )
	
	wikipediaLinkPages = pregen.preload(wikipediaLPages);
	
	i = 0
	for Page in wikipediaLinkPages:
		if Page.exists():
			print "Page \"" + Page.title() + "\" exists on wikipedia."
			wikipediaLinks.append( checkWikipediaLinks[i] )
		else:
			print "Page \"" + Page.title() + "\" does not exist on wikipedia."
			redlinks.append(checkWikipediaLinks[i])
		i += 1
	print redlinks
	
	"""
	"" Edit the page to reflect findings
	"""
	
	for link in wikipediaLinks:
		if linkName(link) == None:
			newLink = "[[w:" + linkURL(link) + "|" + linkURL(link) + "]]"
			newText = newText.replace(link, newLink)
		else:
			newText = newText.replace(link, linkName(link) )

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
