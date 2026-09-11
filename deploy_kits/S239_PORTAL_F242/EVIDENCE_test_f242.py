import os, sys, importlib, json, tempfile
which=sys.argv[1]
d=tempfile.mkdtemp(); store=os.path.join(d,'users.json')
os.environ.update(PORTAL_PIN_HASH='x',PORTAL_PIN_SALT='y',PORTAL_TOKEN_SEED='seed123',CLINIC_SSO_SECRET='s'*40,
  CLINIC_USERS_FILE=store, TILE_GRANTS_FILE='/tmp/pwa/tile_grants_v9.json')
sys.path.insert(0, which)
import clinic_users
clinic_users.add_role(store,'staff'); clinic_users.add_user(store,'manoj','doctor','pw1pw1pw1'); clinic_users.add_user(store,'amir','staff','pw2pw2pw2')
import portal as P
P.STORE=store
c=P.app.test_client()
host='followup.dr-manoj.in'
def show(tag,r): print('  %-44s %s %s'%(tag,r.status_code,r.headers.get('Location','')))
dev=P._expected_device_token()
# 1 stuck browser: device cookie only
c.set_cookie(P.COOKIE_NAME, dev, domain=host, path='/portal')
r=c.get('/portal', base_url='https://'+host); show('device-only GET /portal',r)
r=c.get('/portal/login', base_url='https://'+host); show('device-only GET /portal/login',r)
print('   clears device cookie:', any(P.COOKIE_NAME in h and ('Max-Age=0' in h or 'expires=Thu, 01 Jan 1970' in h) for h in r.headers.getlist('Set-Cookie')))
r=c.get('/portal/casepack', base_url='https://'+host); show('device-only /portal/casepack',r)
# 2 staff login
c2=P.app.test_client()
r=c2.post('/portal/login', data={'user':'amir','password':'pw2pw2pw2'}, base_url='https://'+host); show('amir login',r)
sc=r.headers.getlist('Set-Cookie'); print('   sets sso:', any('clinic_sso=' in h for h in sc), '| plants device cookie:', any(h.startswith(P.COOKIE_NAME+'=') and 'Max-Age=0' not in h and '1970' not in h for h in sc))
r=c2.get('/portal', base_url='https://'+host); show('amir GET /portal',r)
b=r.data.decode(); print('   staff sees Forget/Sign-out-everywhere:', 'Forget all devices' in b, 'Sign out everywhere' in b, '| sign out of this phone:', 'Sign out of this phone' in b)
r=c2.post('/portal/signout-all', base_url='https://'+host); show('amir POST signout-all',r)
r=c2.post('/portal/forget', base_url='https://'+host); show('amir POST forget',r)
print('   epoch now', clinic_users.get_epoch(store))
r=c2.get('/portal/logout', base_url='https://'+host); show('amir GET /portal/logout',r)
r=c2.get('/portal', base_url='https://'+host); show('after logout GET /portal',r)
# 3 doctor
c3=P.app.test_client()
r=c3.post('/portal/login', data={'user':'manoj','password':'pw1pw1pw1'}, base_url='https://'+host); show('manoj login',r)
r=c3.get('/portal', base_url='https://'+host); b=r.data.decode(); show('manoj GET /portal',r); print('   doctor sees buttons:', 'Forget all devices' in b, 'Sign out everywhere' in b)
r=c3.get('/portal/login', base_url='https://'+host); show('manoj GET /portal/login (signed in)',r)
