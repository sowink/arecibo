from django import forms

from app.forms import Form
from app.utils import safe_int, log

from google.appengine.ext import db

from error.models import Error, Group

read_choices = (("", "All"), ("False", 'Read only'), ("True", 'Unread only'))
priority_choices = [ (r, r) for r in range(1, 11)]
priority_choices.insert(0, ("", "All"))

status_choices = ['100', '101', '102', '200', '201', '202', '203', 
'204', '205', '206', '207', '226', '300', '301', '302', '303', '304', 
'305', '307', '400', '401', '402', '403', '404', '405', '406', '407', 
'408', '409', '410', '411', '412', '413', '414', '415', '416', '417',
'422', '423', '424', '426', '500', '501', '502', '503', '504', '505', 
'507', '510']
status_choices = [ (r, r) for r in status_choices ]
status_choices.insert(0, ("", "All"))

err = "You can cannot query on path and start or end dates, this is an App Engine limitation."

class ErrorForm(Form):
    priority = forms.ChoiceField(choices=priority_choices, widget=forms.Select, required=False)
    status = forms.ChoiceField(choices=status_choices, widget=forms.Select, required=False)
    read = forms.ChoiceField(choices=read_choices, widget=forms.Select, required=False)
    start = forms.DateField(required=False, label="Start date", 
        widget=forms.DateInput(attrs={"class":"date",}))
    end = forms.DateField(required=False, label="End date", 
        widget=forms.DateInput(attrs={"class":"date",}))
    query = forms.CharField(required=False, label="Path")
    domain = forms.CharField(required=False)
    uid = forms.CharField(required=False)
    group = forms.CharField(required=False) 
    
    inequality = ""

    def clean(self):
        data = {}
        for k, v in self.cleaned_data.items():
            if not v: continue
            data[k] = v
        
        if "query" in data:
            if "start" in data or "end" in data:
                raise forms.ValidationError(err)
        
        return data
    
    def handle_read(self, value):
        return {"False":False, "True":True}.get(value, None)

    def filter_start(self, value, args):
        return "timestamp >= :%d" % (len(args)+1), [value,]
    
    def filter_end(self, value, args):
        return "timestamp <= :%d" % (len(args)+1), [value,]

    def filter_query(self, value, args):
        self.inequality = "query,"        
        x = len(args)
        return "query >= :%d AND query < :%d" % (x+1, x+2), [value, value + u"\ufffd"]

    def handle_group(self, value):
        return Group.all().filter("uid = ", value)[0].key()
        
    def as_query(self):
        """ This is getting a bit complicated """
        args, gql = [], []
        counter = 1
        
        for k, v in self.cleaned_data.items():
            # if there's a value handler, use it
            lookup = getattr(self, "handle_%s" % k, None)
            if lookup:  v = lookup(v)
            # if there's a filter handler user it
            lfilter = getattr(self, "filter_%s" % k, None)
            if lfilter:
                # will return a filter and args..
                newfilter, newargs = lfilter(v, args)
                gql.append(newfilter)
                args.extend(newargs)
                counter += len(newargs)
            else:
                gql.append(" %s = :%s " % (k, counter))  
                args.append(v)             
                counter += 1
                
        conditions = " AND ".join(gql)
        if conditions: conditions = "WHERE %s" % conditions
        conditions = "SELECT * FROM Error %s ORDER BY %s timestamp DESC" % (conditions, self.inequality)
        query = db.GqlQuery(conditions, *args)
        return query