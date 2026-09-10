"""Corrige les HTML entities dans stats_service.py"""
import html

with open('app/services/stats_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Décoder toutes les HTML entities
fixed = html.unescape(content)

with open('app/services/stats_service.py', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(fixed)

print("OK - HTML entities corrigées dans stats_service.py")

# Vérification syntaxe
import py_compile
try:
    py_compile.compile('app/services/stats_service.py', doraise=True)
    print("OK - Syntaxe Python valide")
except py_compile.PyCompileError as e:
    print(f"ERREUR syntaxe : {e}")

