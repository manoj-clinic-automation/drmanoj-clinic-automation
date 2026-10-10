import hashlib, sys
src, dst = sys.argv[1], sys.argv[2]
b = open(src, 'rb').read()
assert hashlib.md5(b).hexdigest() == '0e9378cd1d9a6da86613bff885b96369', 'FROM pin differs'
s = b.decode('utf-8')
a = '''" · spent "+rs(spent)'''
assert s.count(a) == 1
s = s.replace(a, '''" · spent "+rs(spent)+" (after refunds)"''')
open(dst, 'wb').write(s.encode('utf-8'))
print('built', hashlib.md5(s.encode('utf-8')).hexdigest())
