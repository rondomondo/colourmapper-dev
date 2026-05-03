# colourmapper demo
Output demo/demo.gif
Output demo/demo.mp4

# All Set directives MUST come before any actions
Set Width        1200
Set Height       650
Set FontSize     14
Set FontFamily   "JetBrains Mono"
Set Theme        "Catppuccin Mocha"
Set TypingSpeed  45ms
Set Padding      24
Set Margin       8
Set LineHeight   1.3
Set Shell        "bash"

Require make
Require jq
Require python3

# Suppress venv prompt prefix and set a clean PS1
Hide
Type "export VIRTUAL_ENV_DISABLE_PROMPT=1 && export PS1='\[\033[0;32m\]colourmapper\[\033[0m\] $ ' && clear"
Enter
Sleep 1s
Show

# Section 1: available make targets
Type "make help"
Enter
Sleep 3s

# Section 2: look up a colour name
Sleep 1s
Type "cm 'burnt orange'"
Enter
Sleep 2.5s

# Section 3: look up a colour by hex code
Sleep 1s
Type "cm '#ededed'"
Enter
Sleep 2.5s

# Section 4: short hex code expanded automatically
Sleep 1s
Type "cm '#fff'"
Enter
Sleep 2.5s

# Section 5: nearest-match lookup (no exact entry)
Sleep 1s
Type "cm '#fe0003'"
Enter
Sleep 2.5s

# Section 6: include a preview URL
Sleep 1s
Type "cm --url 'burnt orange'"
Enter
Sleep 2.5s

# Section 7: pipe output to jq
Sleep 1s
Type "cm 'Sapphire' | jq '.hex_value'"
Enter
Sleep 2.5s

# Section 8: pipe a hex lookup and extract the URL
Sleep 1s
Type "cm --url '#3d9970' | jq '.url'"
Enter
Sleep 2.5s

# Section 9: show path to bundled colour map
Sleep 1s
Type "cm --map-file"
Enter
Sleep 2.5s

# Section 10: run the examples target (name + mapping-file preview)
Sleep 1s
Type "make examples"
Enter
Sleep 10s

# End
Sleep 1.5s
