cd new-subs
for h in *.html; do n=${h%.*}; if [ -n "$(ls $n.*zip 2>/dev/null)" ]; then echo exists $n; rm $h; else echo not $n; fi; done 
