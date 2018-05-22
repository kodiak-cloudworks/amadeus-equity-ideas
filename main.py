#
#    Project:   Cloudworks Central
#    Module:    main.py
#    Author:    Som Sikdar
#    This is the main router for the Cloudworks Central portal. It runs on GAE.
#
#copied from google cloud - 5.21.2018      ssikdar
#    
#
from __builtin__ import False

# Import the Flask Framework
from flask import Flask, url_for, redirect
from flask import request, render_template, jsonify
from google.appengine.api import memcache, app_identity
from google.appengine.api import namespace_manager
import datetime, json, requests, yaml, base64, hashlib, time

import jinja2
from jinja2 import Environment, BaseLoader, TemplateNotFound


#    Need the following to make 'reqsuests' work in app engine
from requests_toolbelt.adapters import appengine
# from telnetlib import STATUS
appengine.monkeypatch() # :-)


ProjectID       = app_identity.get_application_id()
versionkey      = '1726.300'        
redirect2info   = 'http://info.kodiakdata.com'
wtok        = ''
Notloggedin =   'Not '



# The secret key is used by Flask to encrypt session cookies.
# SECRET_KEY = 'secret'
# DATA_BACKEND = 'datastore'

#    Get on with the app
cmonapp = Flask(__name__)




#    Initialize the appkeys BEFORE importing from other modules
#
#     Get the keys and params for the application
def getappkey(keyfilename):
    with open(keyfilename) as keyfile: 
        keys = json.load(keyfile)
    return keys
    
appkeys = getappkey('json/appkeys.json')    # imported and used by other modules
ProjectKeys = getappkey('json/' + ProjectID + '.json' )
# Add/replace project specific items in appkeys
for item in ProjectKeys :
        appkeys[ item ] = ProjectKeys[ item ]
pass



redirect2form   = appkeys["redirect2form"] 
gitstuff = appkeys [ "git-template"]
productname = appkeys [ "productname"]
brandname   = appkeys [ "brandname"]   
brandlogo   = appkeys[ 'brandlogo']
apipoint    = appkeys[ 'apipoint' ]


def assertnamespace() :
    thisnamespace = appkeys["gae-namespace"]
    return namespace_manager.set_namespace(thisnamespace)



@cmonapp.route('/kda/mgtest')
def rawfetch(url=''):
#    myString = "https://raw.githubusercontent.com/kodiak-cloudworks/ix-systems/cloudworks/democlient-cred-email.html"
    response = requests.get(    url,
        auth=("token", gitstuff[ "githubapikey"]),
        data={ }
          )
    return response.text



def gitfetch (gitstuff, repofile ):
    response = requests.get(
        gitstuff[ "githubapi" ] + repofile,
        auth=("token", gitstuff[ "githubapikey"]),
        data={ }
          )
    x=  response.json()
    return  base64.b64decode( x['content'] ) if 'content' in x else None 

#initialize the mainrepo

def initmainrepo() :
    mainrepo = yaml.load( gitfetch( gitstuff, gitstuff[ "git-template-repo" ] + 'repo.yaml' ) )
    return mainrepo

  
#
#---- model.py can not be imported earlier due to dependencies
#

import model
from model import Contact, cworksUser

##    Other helper routines
muser   = Notloggedin
def checklogin( wtok = None ):
    if wtok is None :
        muser = Notloggedin              
    else:
        muser = memcache.get(key=wtok)
        wtok = None if muser is None else wtok
    pass
    return wtok


# Generate Secure Link to Demo
def getSecureLink():
    secret = "amadeusequity"
    expires = int(time.time()) + 3900

    slink = "{expires} {secret}".format(expires=expires, secret=secret)

    md5 = hashlib.md5(slink).digest()
    base64url = base64.urlsafe_b64encode(md5).rstrip('=')

    secure_link = "http://amadeus-equity-ideas.demo.memcloud.works:8080/equity-demo/" + base64url + "/" + str(expires) + "/"
    return secure_link


# Routes

@cmonapp.route('/')
def root():
#    return cmonapp.send_static_file('index.html')  
    assertnamespace()
    wtok = checklogin( request.args.get("wt") )
    showhelp = True if 'help' in request.args else False    
    mainrepo = [] #initmainrepo()
    mcrepo =    mainrepo['cloud-services']  if 'cloud-services' in mainrepo else []
    screpo =    mainrepo['storage-services'] if 'storage-services' in mainrepo else []
    demorepo =  mainrepo['demos'] if 'demos' in mainrepo else []
    dbrepo =    mainrepo['database-services'] if 'database-services' in mainrepo else []
    anarepo =   mainrepo['misc'] if 'misc' in mainrepo else []   
    myrepo =    mainrepo['myrepo'] if 'myrepo' in mainrepo else []  
    testrepo =  mainrepo['testdrives'] if 'testdrives' in mainrepo else []     
    sandrepo =  mainrepo['sandboxes'] if 'sandboxes' in mainrepo else [] 
    benchrepo = mainrepo['benchmarks'] if 'benchmarks' in mainrepo else []      
      
    contacts = appkeys['projectkeys'][ProjectID]['contacts']

     
    if not wtok :
        showbanner = True if "prelogin" in appkeys['bannerstring'] else False
        banner = rawfetch( appkeys['bannerstring']['prelogin'] ) if showbanner else ''
        secure_link = getSecureLink()
        return render_template( "index-view.html", wtok = '', secure_link = secure_link, apipoint = apipoint, 
                showbanner = showbanner, banner = banner,
                mcrepo = mcrepo, screpo = screpo, 
                dbrepo = dbrepo, anarepo = anarepo,
                testrepo = testrepo, demorepo = demorepo, myrepo = myrepo, sandrepo= sandrepo, benchrepo = benchrepo,
                contacts = contacts,
                redurl = request.url_root,
                productname = productname, brandname = brandname, brandlogo = brandlogo,
                muser = Notloggedin,
                showhelp = showhelp)  
    else :
        muser = memcache.get(key=wtok)
        userquery = cworksUser.query(cworksUser.mail == muser)
        thisuser = userquery.get()   
        docks = thisuser.docks if thisuser else []
        docklist = []
        for zz in docks :
            zzval = zz.get()
            docklist.append( { "name" : zzval.name, "dock-key" : zz.id(), 
                    "uid" :  zzval.uid, ##    Get the last 4 charadters of uid
                    "type" : zzval.type  } )            
        pass
    

    pass
    showbanner = True if "loggedin" in appkeys['bannerstring'] else False
    banner = rawfetch( appkeys['bannerstring']['loggedin'] ) if showbanner else ''
    
    return  render_template( 'usermain-view.html',   apipoint = apipoint, showbanner = showbanner, banner = banner,
                mcrepo = mcrepo, screpo = screpo, 
                dbrepo = dbrepo, anarepo = anarepo,
                testrepo = testrepo, demorepo = demorepo, myrepo = myrepo, sandrepo= sandrepo, benchrepo = benchrepo,
                contacts = contacts,
                productname = productname, brandname = brandname, brandlogo = brandlogo, 
                docklist = docklist,
                wtok = wtok, redurl = request.url_root, user = muser )    
    

@cmonapp.route('/kda/gitreload', methods = ['GET'])  
def git_reload( ):    
    mainrepo = yaml.load(gitfetch(gitstuff, gitstuff[ "git-template-repo" ] + 'repo.yaml' ))
    return json.dumps(  mainrepo )
  

# send_static_file will guess the correct MIME type
@cmonapp.route('/<path:path>')
def static_proxy(path):
    return cmonapp.send_static_file(path)
    
@cmonapp.route('/kda/version')
def kdaversion():
    wtok = checklogin( request.args.get("wt") )
    assertnamespace()
    return render_template( 'admsg.html', message= appkeys['apptitle'] + ':' + versionkey + '- Dated:' +
                datetime.datetime.utcnow().strftime('%m/%d/%Y') + ' Zulu' + '::' + namespace_manager.get_namespace() + '::',
                                 productname = productname, brandname = brandname ,
                                 brandlogo = brandlogo ,
                redurl = '/', wtok = wtok if wtok else '', muser = memcache.get(key=wtok) if wtok else 'Not logged in', tout= 10 )
    
@cmonapp.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, Nothing at this URL.', 404

@cmonapp.errorhandler(500)
def application_error(e):
    """Return a custom 500 error."""
    return 'Sorry, unexpected error: {}'.format(e), 500

#    -----------------------------------------------

