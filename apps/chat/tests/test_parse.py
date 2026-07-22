import re

def parse_line(line):
    if "|" not in line: return None
    
    parts = line.split("|", 1)
    msg_type = parts[0].strip()
    content = parts[1].strip()
    
    print(f"\nScanning: '{content}'")
    
    # Current (Broken) Regex
    print("--- OLD REGEX ---")
    tokens_old = re.findall(r'(\S+?)(?:\[(.*?)\])?(?=\s|$)', content)
    for word, phonetic in tokens_old:
        word = word.replace('[', '').replace(']', '')
        print(f"W: '{word}' | P: '{phonetic}'")

    # New Approach: Pre-process then split
    print("--- NEW LOGIC ---")
    
    # 1. Ensure space after closed bracket if missing (fix clumped words)
    # e.g. "word[phon]next[phon]" -> "word[phon] next[phon]"
    content_fixed = re.sub(r'\](?=\S)', '] ', content)
    
    raw_tokens = content_fixed.split()
    results = []
    
    for token in raw_tokens:
        # Find phonetic block [....]
        phon_match = re.search(r'\[(.*?)\]', token)
        if phon_match:
            phonetic = phon_match.group(1)
            # Remove the phonetic block from the word
            word = token.replace(phon_match.group(0), "")
        else:
            phonetic = ""
            word = token
            
        results.append((word, phonetic))
        print(f"W: '{word}' | P: '{phonetic}'")

# Test cases based on hypothesis and screenshot
cases = [
    "Yes | Yes[YES] think[THINK] it[it].", # Standard
    "Yes | Yes[YES], I[YI] think[THINK].", # Punctuation attached
    "Yes | Yes[YES],I[YI]think[THINK].",   # Missing spaces entirely
    "Natural | challengingCHAL-ihnj-ing.", # Missing brackets? or malformed
    "Narrative | word[phon].",             # End of line punct
]

for c in cases:
    parse_line(c)
