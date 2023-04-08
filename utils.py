import numpy as np
import datetime
import re
import itertools
import ast
import settings

roles = ['t','j','m','a','s']
valid_roleprefs = ['f']
for i in range(1,len(roles)+1):
    combos = [''.join(sorted(list(x))) for x in itertools.combinations(roles,i)]
    valid_roleprefs.extend(combos)

def check_valid_role(input):
    if ''.join(sorted(input)) in valid_roleprefs:
        rolepref = input
    elif re.match("^[0-9]{5}$",input) is not None:
        rolepref = input
    else:
        rolepref = None
    return rolepref

def prefix_cmd(message,cmd):
    return cmd in message.content[:len(cmd)]

def check_admin(message):
    is_admin = np.any([r.name=='Admin' for r in message.author.roles])
    return is_admin

def is_orca_working():
    now = datetime.datetime.now()
    shift_start = datetime.time(19,30,0,0)
    shift_end = datetime.time(8,0,0,0)
    #first half of shift
    waging = False
    if now.weekday() in [2,3,4]:
        if now.time()>=shift_start:
            waging = True
    #second half
    if now.weekday() in [3,4,5]:
        if now.time()<=shift_end:
            waging = True
    #every other sat
    ww = datetime.datetime.now().isocalendar().week
    if ww%2==0:
        if now.weekday() in [5]:
            if now.time()>=shift_start:
                waging=True
    if ww%2==1:
        if now.weekday() in [6]:
            if now.time()<=shift_end:
                waging=True
    return waging

def participant_parse(arg):
    participants=[]
    p=''
    depth = 0
    for l in arg:
        if l == '(':
            depth += 1
        if l == ')':
            depth -= 1
        if depth == 0:
            if l==',':
                participants.append(p)
                p = ''
                continue
        p+=l
    participants.append(p)
    for i,p in enumerate(participants):
        if "," in p:
            participants[i] = ast.literal_eval(p.strip())
        else:
            participants[i] = p.strip()
    participants = [get_proper_name(p) for p in participants]
    return participants

#get proper spacing/capitalization
def get_proper_name(ign):
    if not isinstance(ign, str):
        return ign
    raw_ign = ign.replace(' ','').lower()
    for i, true_ign in settings.SMURFS.items():
        raw_key = true_ign.replace(' ','').lower()
        if raw_ign == raw_key:
            return true_ign
    for true_ign, r in settings.PLAYER_ROLE_PREF.items():
        raw_key = true_ign.replace(' ','').lower()
        if raw_ign == raw_key:
            return true_ign
    return ign
