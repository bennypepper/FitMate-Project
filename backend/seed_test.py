from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=5000)
db = client['fitmate_db']
col = db['tcm_ingredients']
col.delete_many({})
docs = [
  {'mandarin_name': '人参', 'indonesian_name': 'Ginseng', 'is_toxic': False, 'toxicity_class': 'safe', 'source_reference': 'SymMap'},
  {'mandarin_name': '当归', 'indonesian_name': 'Angelika Cina', 'is_toxic': False, 'toxicity_class': 'safe', 'source_reference': 'SymMap'},
  {'mandarin_name': '甘草', 'indonesian_name': 'Licorice', 'is_toxic': False, 'toxicity_class': 'safe', 'source_reference': 'SymMap'},
  {'mandarin_name': '草药', 'indonesian_name': 'Herba Campuran', 'is_toxic': False, 'toxicity_class': 'safe', 'source_reference': 'BPOM'},
  {'mandarin_name': '大黄', 'indonesian_name': 'Kelembak', 'is_toxic': True, 'toxicity_class': 'toxic', 'target_organ': 'Ginjal', 'source_reference': 'SymMap', 'effects': 'Kerusakan ginjal jika berlebihan'},
  {'mandarin_name': '附子', 'indonesian_name': 'Aconit', 'is_toxic': True, 'toxicity_class': 'highly_toxic', 'target_organ': 'Jantung', 'source_reference': 'SymMap', 'effects': 'Aritmia jantung — berbahaya'},
  {'mandarin_name': '雄黄', 'indonesian_name': 'Realgar (Arsenik)', 'is_toxic': True, 'toxicity_class': 'highly_toxic', 'target_organ': 'Hati, Ginjal', 'source_reference': 'BPOM-terlarang', 'effects': 'Dilarang BPOM — mengandung arsenik'},
  {'mandarin_name': '朱砂', 'indonesian_name': 'Cinnabar (Merkuri)', 'is_toxic': True, 'toxicity_class': 'highly_toxic', 'target_organ': 'Otak, Ginjal', 'source_reference': 'BPOM-terlarang', 'effects': 'Dilarang BPOM — merkuri neurotoksik'},
]
r = col.insert_many(docs)
print('Inserted:', len(r.inserted_ids), 'Total:', col.count_documents({}))
client.close()
