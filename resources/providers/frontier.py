import sys
import xbmc, xbmcplugin, xbmcgui, xbmcaddon
import re, os, time
import urllib, urllib2, httplib2
import json
import HTMLParser
import time
import cookielib
import base64
import string, random
from resources.globals import *



class FRONTIER():    

    def GET_IDP(self):        
        if not os.path.exists(ADDON_PATH_PROFILE):
            os.makedirs(ADDON_PATH_PROFILE)
        
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        
        #IDP_URL= 'https://sp.auth.adobe.com/adobe-services/authenticate?requestor_id=nbcsports&redirect_url=http://stream.nbcsports.com/nbcsn/index_nbcsn-generic.html?referrer=http://stream.nbcsports.com/liveextra/&domain_name=stream.nbcsports.com&mso_id=TWC&noflash=true&no_iframe=true'
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Language", "en-us"),
                            ("Proxy-Connection", "keep-alive"),
                            ("Connection", "keep-alive"),
                            ("User-Agent", UA_IPHONE)]
        
        resp = opener.open(IDP_URL)
        idp_source = resp.read()
        resp.close()
        #print idp_source
        #cj.save(ignore_discard=True);                
        SAVE_COOKIE(cj)

        idp_source = idp_source.replace('\n',"")        

        saml_request = FIND(idp_source,'<input type="hidden" name="SAMLRequest" value="','"')
        #print saml_request

        relay_state = FIND(idp_source,'<input type="hidden" name="RelayState" value="','"')

        saml_submit_url = FIND(idp_source,'action="','"')
        
        
        print saml_submit_url
        #print relay_state
        return saml_request, relay_state, saml_submit_url
    
    def LOGIN(self, saml_request, relay_state, saml_submit_url):
        ###################################################################
        #Post SAML Request & Relay State to get requestId
        ###################################################################       

        url = 'https://tveverywhere.clearleap.com/cltve/olca/authenticate'
        #cj = cookielib.LWPCookieJar()
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Encoding", "gzip, deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded"),
                            ("Proxy-Connection", "keep-alive"),
                            ("Connection", "keep-alive"),
                            ("Origin", "https://sp.auth.adobe.com"),
                            ("Referer", IDP_URL),
                            ("User-Agent", UA_IPHONE)]

        
        data = urllib.urlencode({'SAMLRequest' : saml_request,
                                   'RelayState' : relay_state
                                   })
        
        
        resp = opener.open(url, data)
        print resp.getcode()
        print resp.info()
        print "URL"
        print resp.geturl()
        #idp_source = resp.read()
        if resp.info().get('Content-Encoding') == 'gzip':
            buf = StringIO(resp.read())
            f = gzip.GzipFile(fileobj=buf)
            idp_source = f.read()
        else:
            idp_source = resp.read()
            
        resp.close()
        SAVE_COOKIE(cj)        
        
        request_id = FIND(idp_source,'<input type="hidden" name="requestId" value="','"')

    
        ###################################################################
        #Post username and password to idp        
        ###################################################################

        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)

        url = 'https://tveverywhere.clearleap.com/cltve/auth/authenticate'        
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Encoding", "gzip, deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded"),
                            ("Proxy-Connection", "keep-alive"),
                            ("Connection", "keep-alive"),
                            ("Origin", "https://tveverywhere.clearleap.com"),
                            ("Referer", "https://tveverywhere.clearleap.com/cltve/olca/authenticate"),
                            ("User-Agent", "Mozilla/5.0 (iPhone; CPU iPhone OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Mobile/12H143")]

        
        login_data = urllib.urlencode({'requestId' : request_id,
                                       'username' : USERNAME,
                                       'password' : PASSWORD
                                     })
        
        try:
            resp = opener.open(url, login_data)
            print resp.getcode()
            print resp.info()
            #idp_source = resp.read()
            if resp.info().get('Content-Encoding') == 'gzip':
                buf = StringIO(resp.read())
                f = gzip.GzipFile(fileobj=buf)
                idp_source = f.read()
            else:
                idp_source = resp.read()
                
            resp.close()

            saml_response = FIND(idp_source,'<input type="hidden" id="SAMLResponse" name="SAMLResponse" value="','"')            
            #saml_response = saml_response.replace('&#xd;&#xa;','')
            saml_response = HTMLParser.HTMLParser().unescape(saml_response)        
            #saml_response = urllib.quote(saml_response)


            relay_state = FIND(idp_source,'<input type="hidden" id="RelayState" name="RelayState" value="','"')

        except:
            saml_response = ""
            relay_state = ""
        #Set Global header fields         
        global ORIGIN
        global REFERER
        ORIGIN = 'https://tveverywhere.clearleap.com'
        REFERER = 'https://tveverywhere.clearleap.com/cltve/olca/authenticate'

        print saml_response
        return saml_response, relay_state
