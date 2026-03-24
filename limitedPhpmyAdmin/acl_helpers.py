# -*- coding: utf-8 -*-
from loginSystem.models import Administrator
from plogical.acl import ACLManager
from websiteFunctions.models import Websites
from databases.models import Databases
from ftp.models import Users as FTPUser


def get_session_admin_acl(request):
    user_id = request.session.get('userID')
    if not user_id:
        return None, None, None
    admin = Administrator.objects.get(pk=user_id)
    acl = ACLManager.loadedACL(user_id)
    return user_id, admin, acl


def get_allowed_websites(user_id, acl):
    return ACLManager.findWebsiteObjects(acl, user_id)


def resolve_owned_website(admin, acl, website_id):
    try:
        wid = int(website_id)
    except (TypeError, ValueError):
        return None
    try:
        site = Websites.objects.get(pk=wid)
    except Websites.DoesNotExist:
        return None
    if ACLManager.checkOwnership(site.domain, admin, acl) != 1:
        return None
    return site


def database_on_website(website, db_name):
    if not db_name:
        return None
    try:
        return Databases.objects.get(website=website, dbName=db_name)
    except Databases.DoesNotExist:
        return None


def list_ftp_for_website(website):
    rows = FTPUser.objects.filter(domain=website).order_by('user')
    return [{'id': r.id, 'user': r.user, 'status': r.status} for r in rows]


def list_cpusers_for_website(website):
    admins = []
    owner = website.admin
    admins.append({'id': owner.pk, 'userName': owner.userName})
    for child in Administrator.objects.filter(owner=owner.pk).order_by('userName'):
        admins.append({'id': child.pk, 'userName': child.userName})
    return admins


def resolve_ftp_user(website, ftp_user_id):
    try:
        fid = int(ftp_user_id)
    except (TypeError, ValueError):
        return None
    try:
        fu = FTPUser.objects.get(pk=fid, domain=website)
    except FTPUser.DoesNotExist:
        return None
    return fu


def resolve_cpuser_for_website(website, administrator_id):
    try:
        aid = int(administrator_id)
    except (TypeError, ValueError):
        return None
    try:
        adm = Administrator.objects.get(pk=aid)
    except Administrator.DoesNotExist:
        return None
    if adm.pk == website.admin.pk:
        return adm
    if adm.owner == website.admin.pk:
        return adm
    return None
