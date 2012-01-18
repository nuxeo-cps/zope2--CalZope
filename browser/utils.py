
class LinkProtectable:

    def __init__(self):
        self.protect_links_javascript=self.context.getCalendar().areProtectedLinks()

    def getHref(self, url):
        if not hasattr(self,'protect_links_javascript'):
            self.protect_links_javascript = self.context.getCalendar().areLinksProtected()
        if self.protect_links_javascript:
            return '#'
        return url

    def getOnClick(self, url):
        if not hasattr(self,'protect_links_javascript'):
            self.protect_links_javascript = self.context.getCalendar().areLinksProtected()
        if self.protect_links_javascript:
            return 'window.location="%s"; return false;' % url
        return 
        
    
