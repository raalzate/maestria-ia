import re
import json

def test_parse(raw_text):
    breakdown = []
    lines = raw_text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or '|' not in line:
            continue
        
        matches = re.finditer(r'([^\[|]+)\[([^\]]+)\]', line)
        for match in matches:
            english_phrase = match.group(1).strip()
            spanish_translation = match.group(2).strip()
            print(f"DEBUG - Match: {english_phrase} -> {spanish_translation}")
            
            if english_phrase and spanish_translation:
                breakdown.append({
                    "word": english_phrase,
                    "phonetic": spanish_translation 
                })
    return breakdown

test_input = """I'm glad you're excited[Me alegra que estés emocionado]| to chat[para charlar]|! So[Entonces], I was thinking[Estaba pensando]| what's the most common[¿cuál es lo más común]| way you've used[modo en que has utilizado]| the verb "to be"[el verbo "ser"]| in a sentence[en una oración]| when introducing yourself[al presentarte a ti mismo]| in a language[en un idioma]| other than your native one[distinto al tuyo nativo]|?"""

result = test_parse(test_input)
print("\nFINAL BREAKDOWN:")
print(json.dumps(result, indent=2, ensure_ascii=False))
