import re, sublime

RE_REPLACE_GLOB = re.compile(r"\*\*|[\*\?\.\(\)\[\]\{\}\$\^\+\|]")

region_id = 0

# Colors
FG_ANSI = {
  30: 'black',
  31: 'red',
  32: 'green',
  33: 'brown',
  34: 'blue',
  35: 'magenta',
  36: 'cyan',
  37: 'white',
  39: 'default',
  90: 'light_black',
  91: 'light_red',
  92: 'light_green',
  93: 'light_brown',
  94: 'light_blue',
  95: 'light_magenta',
  96: 'light_cyan',
  97: 'light_white'
}

BG_ANSI = {
    40: 'black',
    41: 'red',
    42: 'green',
    43: 'brown',
    44: 'blue',
    45: 'magenta',
    46: 'cyan',
    47: 'white',
    49: 'default',
    100: 'light_black',
    101: 'light_red',
    102: 'light_green',
    103: 'light_brown',
    104: 'light_blue',
    105: 'light_magenta',
    106: 'light_cyan',
    107: 'light_white'
}

SCOPES = {
  'red':           'redish',
  'green':         'greenish',
  'brown':         'orangish',
  'blue':          'bluish',
  'magenta':       'pinkish', # purplish
  'cyan':          'cyanish',
  'light_red':     'redish',
  'light_green':   'greenish',
  'light_brown':   'orangish',
  'light_blue':    'bluish',
  'light_magenta': 'pinkish',
  'light_cyan':    'cyanish'
}

RE_UNKNOWN_ESCAPES = re.compile(r"\x1b[^a-zA-Z]*[a-zA-Z]")
RE_COLOR_ESCAPES = re.compile(r"\x1b\[((?:;?\d+)*)m")
RE_NOTSPACE = re.compile(r"[^\s]+")

def write(view, characters):
  decolorized = ""
  original_pos = 0
  decolorized_pos = 0
  fg = "default"
  bg = "default"
  regions = []
  def iteration(start, end, group):
      nonlocal decolorized, original_pos, decolorized_pos, fg, bg, regions
      text = characters[original_pos:start]
      text = RE_UNKNOWN_ESCAPES.sub("", text)
      decolorized += text
      if len(text) > 0 and (fg != "default" or bg != "default"):
          regions.append({"text":  text,
                          "start": decolorized_pos,
                          "end":   decolorized_pos + len(text),
                          "fg":    fg,
                          "bg":    bg})
      digits = re.findall(r"\d+", group) or ["0"]
      for digit in digits:
          digit = int(digit)
          if digit in FG_ANSI:
              fg = FG_ANSI[digit]
          if digit in BG_ANSI:
              bg = BG_ANSI[digit]
          if digit == 0:
              fg = 'default'
              bg = 'default'
      original_pos = end
      decolorized_pos += len(text)

  for m in RE_COLOR_ESCAPES.finditer(characters):
      iteration(m.start(), m.end(), m.group(1))
  iteration(len(characters), len(characters), "")

  insertion_point = view.size()
  view.run_command('append', {'characters': decolorized, 'force': True, 'scroll_to_end': True})
  
  global region_id
  for region in regions:
      if scope := SCOPES.get(region['bg'], None) or SCOPES.get(region['fg'], None):
          for m in RE_NOTSPACE.finditer(region['text']):
              start = insertion_point + region['start'] + m.start()
              end = start + len(m.group(0))
              region_id += 1
              view.add_regions(
                          "executor#{}".format(region_id),
                          [sublime.Region(start, end)],
                          'region.' + scope)
