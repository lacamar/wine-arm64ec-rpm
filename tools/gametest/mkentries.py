import sqlite3, time, os, sys
C='/home/lm/.steam/steam/steamapps/common'
L='/home/lm/.local/share/lutris'
W='/home/lm/.local/share/wine-prefixes'
db=sqlite3.connect(L+'/pga.db')
now=int(time.time())
for line in open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'games.tsv')):
    slug,name,exe=line.rstrip('\n').split('\t')
    slug+='-test-claude'; name+=' test-claude'
    exe=f'{C}/{exe}'; assert os.path.exists(exe), exe
    if db.execute('select 1 from games where slug=?',(slug,)).fetchone(): print('exists',slug); continue
    cfg=f'{slug}-{now}'
    open(f'{L}/games/{cfg}.yml','w').write(f"""game:
  exe: {exe}
  prefix: {W}/{slug}
  working_dir: {os.path.dirname(exe)}
system:
  env:
    DISPLAY: ''
    FEX_X87REDUCEDPRECISION: '1'
    MANGOHUD_CONFIGFILE: /home/lm/.config/MangoHud/asahi-test.conf
    PULSE_SINK: claude-test
    WINEDEBUG: -all,+fps,err+seh,err+virtual,err+module
  mangohud: true
  prelaunch_command: ''
wine:
  dxvk: true
  system_winetricks: true
  version: system
""")
    db.execute("insert into games (name,slug,platform,runner,installed,installed_at,configpath,has_custom_banner,has_custom_icon,has_custom_coverart_big,playtime) values (?,?,'Windows','wine',1,?,?,0,0,0,0)",(name,slug,now,cfg))
    print('added',slug)
db.commit()
