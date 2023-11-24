import string, sys, fileinput, getopt, os, glob

def map_category ( catmap, catlist ):
  for cat in catlist.strip().split(';'):
    try:
      mycat = catmap[cat]
    except LookupError:
      mycat = ''
    if mycat != '':
      return mycat
  return 'Other'

def main():
  # Use categories from XDG spec
  catmap = {
  'Development': 'Development',
  'Education': 'Education',
  'Game': 'Games',
  'Graphics': 'Graphics',
  'Internet': 'Internet',
  'Settings': 'Settings',
  'Screensaver': 'Settings',
  'System': 'System',
  'Emulator': 'System',
  'Network': 'Internet',
  'AudioVideo': 'Multimedia',
  'Audio': 'Multimedia',
  'Video': 'Multimedia',
  'Utility': 'Accessories',
  'Accessibility': 'Accessories',
  'Core': 'Accessories',
  'Office': 'Office'}

  cats = list()
  outp = list()
  print('MenuClear(\'Menugen_Applications\')')
  dirlist = os.environ.get('XDG_DATA_DIRS')
  if not dirlist:
    dirlist = '/usr/local/share:/usr/share'
  dhome = os.environ.get('XDG_DATA_HOME')
  if not dhome:
    dhome = os.environ.get('HOME')
    if dhome:
      dhome = dhome + '/.local/share'
  if dhome:
    dirlist = dirlist + ':' + dhome
  dlist = []
  for dir in dirlist.split(':'):
    dlist = dlist + sorted(glob.glob(dir + '/applications/*.desktop'))
  for dfile in dlist:
    de_name = de_icon = de_exec = de_cat = de_disp = ''
    fchan = open(dfile)
    for dline in fchan.readlines():
      try:
        (tag, value) = dline.strip().split('=',1)
        if tag.strip() == 'Name' and not de_name: # Grab first name
          de_name = value.strip()
        if tag.strip() == 'Icon':
          de_icon = value.strip()
        if tag.strip() == 'Exec':
          de_exec = value.strip()
        if tag.strip() == 'Categories':
          de_cat = value.strip()
        if tag.strip() == 'NoDisplay':
          de_disp = value.strip()
      except:
        pass
    fchan.close()
    if (de_name != '') and (de_exec != '') and (de_disp.lower() != 'true'):
      if de_cat.startswith('X-tower-'):
        de_cat = '0_' + de_cat[8:].split(';')[0].capitalize()
      else:
        de_cat = map_category ( catmap, de_cat )
      de_exec = de_exec.replace(' %f','').replace(' %F','').replace(' %u','')
      de_exec = de_exec.replace(' %U','').replace(' %c',' '+de_name)
      de_exec = de_exec.replace(' %k',' '+dfile).replace(' %i',' '+de_icon)
      if not (de_cat in cats):
        cats.append(de_cat)
        print('MenuClear(\'Menugen_' + de_cat.replace('0_', '') + '\')')
        sub_icon = '%applications-' + de_cat.lower()
        if (de_cat.lower() == 'settings'): # these is no applications-settings icon
            sub_icon = '%preferences-system'
        outp.append('Menu(\'Menugen_Applications\') { SubMenu(\'' + de_cat +
        sub_icon + '\',\'Menugen_' + de_cat + '\') }')
      outp.append('Menu(\'Menugen_' + de_cat + '\') { Item(\'' + de_name + '%' +
      de_icon + '\',Exec \'' + de_exec +'\') }')
  for token in sorted(outp):
    print(token.replace('0_', ''))


if __name__ == '__main__':
  main()