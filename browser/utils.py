
class LinkProtectable:
    """
        Mixin for BrowserView for javascript links protection.
    """
    
    protect_links_javascript = None 
        
    def areLinksProtected(self):
        p = self.protect_links_javascript
        if p is None:
            p = self.context.getCalendar().areLinksProtected()
            self.protect_links_javascript = p
            
        return p
        
    def getHref(self, url):
        return self.areLinksProtected() and '#' or url

    def getOnClick(self, url):
        if self.areLinksProtected():
            return 'window.location="%s"; return false;' % url
        return url
        
        
    
