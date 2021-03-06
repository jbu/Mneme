#!/usr/bin/env python
#
#
# this program is using some code from Cherrypy and Personis tutorial

import os, sys

import Personis
import Personis_base
import Personis_a
from Personis_util import printcomplist

#Time, date, timezone
from datetime import date, time, timedelta
import time
#from pytz import timezone, tzfile
#import pytz

# Personis Configuration
#cfg = ConfigParser.ConfigParser()
#cfg.read(os.path.expanduser("~/.personis.conf"))
#personispath = cfg.get('paths', 'personis')
#print "Path:", personispath
#sys.path.insert(0, personispath)

#_curdir = os.path.join(os.getcwd(), os.path.dirname(__file__))

#model_dir = '/home/chai/llum/llum/Personis/models'

#Apps model
from AppList import *

modeltree = []
global index
index = 0
class model_tree(object):
    def __init__(self,name="",parent="",child=[],level=0,expand=False):
        self.name = name
        self.parent = parent
        self.children = child
        self.expand = expand
        self.level = level
        self.visited = 0

class Personis_Access(object):

    # initialise personis um object and access to the server
    def __init__(self, connection=None, debug=0):
        self.connection = connection

        self.um = Personis.Access(connection = self.connection, debug=True)
            # modelfile = "saved-model"
            #print "importing:", modelfile
            #modeljson = open(modelfile).read()
            #self.um.import_model(partial_model=modeljson)

        #self.make_new_component('log-in','attribute', 'string',None,'None')
        #self.make_new_component('browseractivity','attribute', 'string',None,'None')


    # adding new component to the context (default 'Personal')
    def make_new_component(self, cname, ctype, value=None, res=None, desc=None, context=['Personal']):
        try:
            cobj = Personis_base.Component(Identifier=cname, component_type=ctype, Description=desc, value_type=value, resolver=res)
            self.um.mkcomponent(context=context, componentobj=cobj)
            return True
        except Exception, e:
            print e
            return str(e)

    # adding new view to the model to the component list of context 'People'

    def make_new_view(self, vname, context, vcomplist):
        vobj = Personis_base.View(Identifier=vname, component_list=vcomplist)
        print "view:", vname
        self.um.mkview(context=context, viewobj=vobj)


    # adding new evidence to component
    def add_evidence(self, context=[], component=None, value=None, comment=None, usertime=None):
        print component, value
        ev = Personis_base.Evidence(source="Personis_Access.py", evidence_type="explicit", value=value)
        ev.comment = comment
        if usertime:
            import time
            ev.time=time.mktime(time.strptime(usertime, '%Y-%m-%d %H:%M:%S'))
        self.um.tell(context=context, componentid=component, evidence=ev)


    def make_new_context(self,context_id,desc,context=['']):
        try:
            ctx_obj = Personis_base.Context(Identifier=context_id,
                                            Description=desc,
                                            perms={'ask':True, 'tell':True, "resolvers":["all","last10","last1","goal"]},                                                                                           resolver=None, objectType="Context")

            print "Creating new context %s"%context_id
            self.um.mkcontext(context,ctx_obj)
            return "Success"
        except Exception,e:
            print e
            return e


    #-----Adding a component called access record associated to each context and component-----------#

    def set_access_records(self):
        dir_list, main_dirs = self.get_context_list()
        for dirs in main_dirs:
            print dirs
        for d in dir_list:
            print d['dir']
            context_list = d['dir'].split('/')
            self.make_new_component(self.um, "access",'attribute', 'string',None,'None',context_list)

    #----------Creating Application context: Apps model----------------#

    def create_app_context(self):
        try:
            ctx_obj = Personis_base.Context(Identifier="Apps",
                                            Description="Applications available for use",
                                            perms={'ask':True, 'tell':True, "resolvers":["all","last10","last1","goal"]},                                                                                           resolver=None, objectType="Context")
            context = []
            context.append('.')
            print "Creating Applications context "
            self.um.mkcontext(context,ctx_obj)
            return True
        except Exception,e:
            return False

    #-------Accessing the um to ask components and view evidence list

    def all_access_model(self, cont=[]):
        context_list = []
        try:
            info = self.um.ask(context=cont, showcontexts=True)
            (cobjlist, contexts, theviews, thesubs) = info
            #printcomplist(cobjlist, printev = "yes")
            print "Components:"
            for cobj in cobjlist:
                print "\t%s: %s"%(cobj.Identifier, cobj.Description)
            print "Contexts: %s" % str(contexts)
            print "Views: %s" % str(theviews)
            print "Subscriptions: %s" % str(thesubs)

            for dirs in contexts:
                context_list.append(dirs)
            return context_list
        except ValueError, e:
            err_msg = "ask failed: %s" % (e)
            return err_msg


    def get_all_component(self, context=[]):
        try:
            if(context):
                info = self.um.ask(context=context,view=None,resolver=None,showcontexts=True)
                cobjlist,contexts,view,subs = info
                print info
                for t in contexts:
                    print t
                new_cobjlist = list()
                for c in cobjlist:
                    print c.Identifier
                    if c.Identifier[0] != '@':
                        new_cobjlist.append(c)
                return contexts, new_cobjlist
        except Exception,e:
            print e
            return str(e),str(e)


    def todict(self, obj, classkey=None):
        if isinstance(obj, dict):
            for k in obj.keys():
                obj[k] = self.todict(obj[k], classkey)
            return obj
        elif hasattr(obj, "__iter__"):
            return [self.todict(v, classkey) for v in obj]
        elif hasattr(obj, "__dict__"):
            data = dict([(key, self.todict(value, classkey))
              for key, value in obj.__dict__.iteritems()
              if not callable(value) and not key.startswith('_')])
            if classkey is not None and hasattr(obj, "__class__"):
                data[classkey] = obj.__class__.__name__
            return data
        else:
            return obj

    #cur_level = 0
    def expand_model(self, context_name, context, cur_level):
        global index
        info = self.um.ask(context=context,view=None,resolver=None,showcontexts=True)
        cobjlist,subcontexts,view,subs = info
        if len(subcontexts) == 0:
            modeltree.append(model_tree(context_name,parent=context[:-1],child=subcontexts,level=cur_level,expand=False))
            return
        else:
            modeltree.append(model_tree(context_name,parent=context[:-1],child=subcontexts,level=cur_level,expand=True))
            for i in range(len(sorted(subcontexts))):
                cur_level += 1
                context.append(subcontexts[i])
                self.expand_model(subcontexts[i],context,cur_level)
                context.remove(subcontexts[i])
                cur_level -= 1

    def build_modeldef_tree(self):
        del modeltree[:]

        context = []
        info = self.um.ask(context=context,view=None,resolver=None,showcontexts=True)
        cobjlist,contexts,view,subs = info
        #index = len(contexts)
        for i in range(len(sorted(contexts))):
            context = []
            context.append(contexts[i])
            cur_level = 0
            self.expand_model(contexts[i], context, cur_level)
            #context.remove(contexts[i])

        return modeltree

    def get_context(self, context=['Personal'], getSize=True):
        try:
            print context, getSize
            contextinfo = self.um.getcontext(context=context, getsize=getSize)
            return contextinfo
        except Exception, e:
            #print e
            return str(e)

    def get_evidence_new(self, context=['Personal'], componentid='firstname',resolver={'evidence_filter':"all"}):
        try:
            print context,componentid
            info = self.um.ask(context=context,view=None,resolver=resolver,showcontexts=True)
            cobjlist,contexts,view,subs = info
            evdlist = list()
            for c in cobjlist:
                if c.Identifier == componentid:
                    if c.evidencelist:
                        for item in c.evidencelist:
                            evdlist.append(item)

            return evdlist
        except Exception,e:
            print e
            return e

    def getpermission(self, context, app):
        perms = self.um.getpermission(context=["Devices"], app=app)
        return perms

    #get todays date and time

    def get_date(self):
        try:
            t = datetime.now()
            print t
            EpochSeconds=time.mktime(t.timetuple())
            #now = datetime.fromtimestamp(EpochSeconds, pytz.utc )
            #now = now.astimezone(pytz.timezone('Australia/Sydney'))
            print "Now %s"%now
            return now
        except Exception, e:
            return e

    def um_applist(self):
        return self.um.listapps()


    #add new evidence

    def add_new_evidence(self,context, data=None):
        try:
            print data, context
            componentid,value,flags,comment,user_date,useby_date =data.split("_")
            context = context.split("/")
            ev = Personis_base.Evidence(source=self.username, evidence_type="explicit", value=value)
            if comment != 'None': ev.comment=comment
            if flags != 'None': ev.flags = flags
            if user_date != 'None': ev.time=time.mktime(time.strptime(user_date, '%d/%m/%Y'))
            if useby_date != 'None': ev.useby=time.mktime(time.strptime(useby_date, '%d/%m/%Y'))
            self.um.tell(context=context, componentid=componentid, evidence=ev)
            return True
        except Exception,e:
            return False

    #---------------------- Functions for deletion -------------------------------------#

    def delete_component(self, context, component):
        resd = self.um.delcomponent(context, componentid)
        return resd

    def delete_context(self, context):
        if self.um.delcontext(context):
            return "ok"
        else:
            return "fail"

    def delete_view(self, context, viewid):
        try:
            self.um.delview(context, viewid)
            return "ok"
        except Exception, e:
            return "fail:"+str(e)

    #---------------------- Functions for subscription or rules -------------------------------------#

    def add_rules(self, context):
        sub = """
         ["*/30 * * * *"] <default!./Goals/StepGoal> ~ '.*' :
                 NOTIFY 'http://vm1-chai2.cs.usyd.edu.au:2001/get_fitbit_data'  """

        result = self.um.subscribe(context=["Personal"], view=['lastname'], subscription={'user':'alice', 'password':'secret', 'statement':sub})
        print result


    #------------------Deprecated Functions (not used)----------------------------------#

    #accessing the um to add personal components (firstname and lastname) and tell evidence
    def tell_model(self, modelname, username, fname, lname, sex, password):
        # create a new components
        # tell this as user's first name, last name and gender
        ev = Personis_base.Evidence(source=self.username, evidence_type="explicit", value=fname)
        self.um.tell(context=["Personal"], componentid='firstname', evidence=ev)
        ev = Personis_base.Evidence(source=self.username, evidence_type="explicit", value=lname)
        self.um.tell(context=["Personal"], componentid='lastname', evidence=ev)
        ev = Personis_base.Evidence(source=self.username, evidence_type="explicit", value=sex)
        self.um.tell(context=["Personal"], componentid='gender', evidence=ev)


    def tell_login_time(self, comp_id):

        try:
            time = datetime.now()
            ev = Personis_base.Evidence(source="build_model.py", evidence_type="explicit", value=time)
            self.um.tell(context=["Personal"], componentid=comp_id, evidence=ev)
        except Exception, e:
            print e
            return e


    def add_access_records(self,componentid=None):
        try:
            self.um = Personis.Access(connection = self.connection, debug=True)
            ev = Personis_base.Evidence(source="build_model.py", evidence_type="explicit", value=str(componentid))
            ev.comment = "Access Record for " + componentid
            context = self.__curContext.split('/')
            self.um.tell(context=context, componentid="access", evidence=ev)
            return "Success"
        except Exception,e:
            print e
            return "Error "+e


    def get_size(self):
        model = self.modelname.split('@')
        import subprocess
        ret = subprocess.call(["ssh", "chai@vm1-chai2", "python /home/chai/Personis-155/Personis/Src/getSize.py "+model[0]]);
        return ret

    def get_evidence_fitbit(context, componentid, start, end):
        evdlist = self.get_evidence_new(context, component)
        days_in_between = str(end - start).split(' ')
        interval = int(days_in_between[0])
        print interval
        margin = datetime.timedelta(days = interval)
        keys = ('date','steps')
        for ev in evdlist:
            #print datetime.datetime.fromtimestamp(int(ev.time)).strftime('%Y-%m-%d'), ev.value

            try:
                um_time = ev.time
                import datetime
                tt = time.localtime(int(um_time))
                track_date = date(tt[0],tt[1],tt[2])
                if start <= track_date <= end:
                    #datetime.datetime.fromtimestamp(int(time)).strftime('%Y-%m-%d')
                    if prev_date != track_date:
                        if newval != 0:
                            new_evdlist.append(newval)
                            datelist.append(track_date)
                            print "UM data on %s is %s"%(str(track_date), newval)
                        newval = int(ev.value)

                        prev_date = track_date
                    else:
                        newval = newval + int(ev.value)

            except Exception,e:
                print e
                return "Error: "+str(e)

            dict_data = []

            for i in range(len(new_evdlist)):
                tag_list=list()
                tag_list.append(datelist[i])
                tag_list.append(new_evdlist[i])
                data_dictionary = dict(itertools.izip(keys, tag_list))
                dict_data.append(data_dictionary)
        return dict_data
