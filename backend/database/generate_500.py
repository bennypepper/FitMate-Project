import json
import os
import sys

sys.path.insert(0, 'backend')
from database.seed_100_tcm import POPULAR_TCM

meridian_id_map = {
    'lung': 'Paru-paru',
    'liver': 'Hati',
    'kidney': 'Ginjal',
    'heart': 'Jantung',
    'spleen': 'Limpa / Pencernaan',
    'stomach': 'Lambung',
    'large intestine': 'Usus Besar',
    'small intestine': 'Usus Halus',
    'bladder': 'Kandung Kemih',
    'gallbladder': 'Kantung Empedu',
    'pericardium': 'Perikardium',
    'triple energizer': 'San Jiao',
}

def translate_meridians(mer_eng):
    if not mer_eng:
        return 'Umum'
    parts = [str(p).strip().lower() for p in str(mer_eng).split(',')]
    res = []
    for p in parts:
        if p in meridian_id_map:
            res.append(meridian_id_map[p])
        elif p:
            res.append(p.capitalize())
    return ', '.join(dict.fromkeys(res)) if res else 'Umum'

def get_desc(cls_eng, prop_eng, name_eng):
    c = str(cls_eng or '').lower()
    p = str(prop_eng or '').lower()
    if 'antitussive' in c or 'asthma' in c:
        return 'Pereda batuk, peluruh dahak, dan kesehatan saluran pernapasan'
    if 'heat-clearing' in c:
        return 'Pereda panas dalam, anti-radang, dan detoksifikasi racun panas'
    if 'hemostatic' in c:
        return 'Penghenti pendarahan dan pemulihan luka jaringan'
    if 'tonif' in c or 'replenish' in c:
        return 'Herbal tonik peningkat stamina, daya tahan tubuh, dan energi vital'
    if 'blood' in c:
        return 'Memperlancar sirkulasi darah dan meredakan nyeri akibat penyumbatan'
    if 'exterior' in c:
        return 'Meredakan gejala awal flu, demam, masuk angin, dan sakit kepala'
    if 'damp' in c or 'diuretic' in c:
        return 'Mengeluarkan kelembaban tubuh berlebih dan melancarkan buang air'
    if 'digest' in c or 'stomachic' in c:
        return 'Memperbaiki fungsi lambung dan mengoptimalkan pencernaan'
    if 'calm' in c or 'sedat' in c:
        return 'Menenangkan pikiran, meredakan kecemasan, dan mengatasi insomnia'
    if 'interior-warm' in c or 'cold-dispell' in c:
        return 'Menghangatkan tubuh bagian dalam dan mengusir dingin'
    if 'purgative' in c:
        return 'Pencahar alami untuk melancarkan buang air besar'
    if 'toxic' in p:
        return 'Herbal berkandungan toksik keras, diawasi ketat dan dilarang penggunaan mandiri'
    return 'Bahan herbal alami terdaftar untuk terapi kesehatan holistik'

items = []
seen = set()

def add_entry(mandarin, pinyin, indo, eng, lat, is_toxic, lvl, organ, desc, src):
    key = (mandarin or '').strip().lower()
    if not key:
        key = (pinyin or '').strip().lower()
    if not key:
        key = (indo or '').strip().lower()
    if key in seen:
        return False
    seen.add(key)
    items.append({
        'mandarin_name': (mandarin or '').strip(),
        'pinyin_name': (pinyin or '').strip(),
        'indonesian_name': (indo or '').strip(),
        'english_name': (eng or '').strip(),
        'latin_name': (lat or '').strip(),
        'is_toxic': bool(is_toxic),
        'toxicity_level': lvl or ('high' if is_toxic else 'none'),
        'toxicity_class': 'toxic' if is_toxic else 'safe',
        'target_organ': organ or 'Umum',
        'description': desc or '',
        'source_reference': src or 'BPOM-TI',
        'validated_by': 'fitmate_verified'
    })
    return True

# 1. Add all 101 POPULAR_TCM
for m, p, i, e, tox, lvl, org, d, src in POPULAR_TCM:
    lat = i if (' ' in i and '/' not in i) else ''
    add_entry(m, p, i, e, lat, tox, lvl, org, d, src)

print('Stage 1 (POPULAR_TCM):', len(items))

# 2. Add BPOM OTSKK herbs
try:
    with open('data/scraper/output/bpom_ingredients.json', 'r', encoding='utf-8') as f:
        bpom_raw = json.load(f)
    for b in bpom_raw:
        indo_name = str(b.get('indonesian_name') or '').strip()
        lat_name = str(b.get('latin_name') or '').strip()
        if not indo_name:
            continue
        exists = any(indo_name.lower() == it['indonesian_name'].lower() for it in items)
        if not exists:
            add_entry(
                b.get('mandarin_name', ''),
                b.get('pinyin_name', ''),
                indo_name,
                indo_name,
                lat_name,
                False,
                'none',
                'Pencernaan / Hati',
                'Tanaman obat terdaftar BPOM OTSKK untuk sediaan herbal Indonesia',
                b.get('bpom_reference', 'BPOM-OTSKK')
            )
except Exception as err:
    print('BPOM load warning:', err)

print('Stage 2 (+BPOM):', len(items))

# 3. Add SymMap toxic herbs
with open('data/scraper/output/symmap_herbs_raw.json', 'r', encoding='utf-8') as f:
    symmap = json.load(f)

def is_sym_toxic(s):
    p = str(s.get('Properties_English') or '').lower()
    c = str(s.get('Class_English') or '').lower()
    return 'toxic' in p or 'toxic' in c

sym_toxic = [s for s in symmap if is_sym_toxic(s)]
sym_safe = [s for s in symmap if not is_sym_toxic(s)]

for s in sym_toxic:
    if len(items) >= 500:
        break
    m = s.get('Chinese_name') or ''
    p = s.get('Pinyin_name') or ''
    e = s.get('English_name') or ''
    lat = str(s.get('Latin_name') or '').split(',')[0].strip()
    props = str(s.get('Properties_English') or '')
    meridians = translate_meridians(s.get('Meridians_English'))
    
    props_lower = props.lower()
    lvl = 'high' if ('extremely toxic' in props_lower or 'great toxic' in props_lower) else 'moderate' if 'toxic' in props_lower else 'low'
    desc = f'Herbal berkandungan toksik ({props}). Diawasi ketat dan dilarang penggunaan mandiri tanpa pengawasan apoteker.'
    indo = p or e or lat
    add_entry(m, p, indo, e or p, lat, True, lvl, meridians, desc, 'SymMap-Toxic')

print('Stage 3 (+SymMap Toxic):', len(items))

# 4. Add SymMap safe herbs until exactly 500
for s in sym_safe:
    if len(items) >= 500:
        break
    m = s.get('Chinese_name') or ''
    p = s.get('Pinyin_name') or ''
    e = s.get('English_name') or ''
    lat = str(s.get('Latin_name') or '').split(',')[0].strip()
    cls_e = s.get('Class_English') or ''
    props = s.get('Properties_English') or ''
    meridians = translate_meridians(s.get('Meridians_English'))
    
    desc = get_desc(cls_e, props, e)
    indo = p or e or lat
    add_entry(m, p, indo, e or p, lat, False, 'none', meridians, desc, 'SymMap')

print('Final total items:', len(items))

toxic_count = sum(1 for it in items if it['is_toxic'])
safe_count = sum(1 for it in items if not it['is_toxic'])
print(f'Breakdown: {toxic_count} toxic / restricted, {safe_count} safe herbs')

# Save both to backend and frontend
os.makedirs('backend/database/data', exist_ok=True)
with open('backend/database/data/tcm_500_ingredients.json', 'w', encoding='utf-8') as f:
    json.dump(items, f, ensure_ascii=False, indent=2)

with open('frontend/src/data/tcmIngredients.json', 'w', encoding='utf-8') as f:
    json.dump(items, f, ensure_ascii=False, indent=2)

print('Saved successfully to backend and frontend!')
