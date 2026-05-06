"""
seed_100_tcm.py — Seed MongoDB with 100 Popular TCM ingredients in Indonesia
Bypasses Excel to directly inject validated dummy entries for testing and PoC.
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import asyncio
from pydantic import ValidationError
from backend.database.mongodb import get_db, create_indexes
from backend.database.schemas import TCMIngredient
from motor.motor_asyncio import AsyncIOMotorClient

POPULAR_TCM = [
    ("罗汉果", "Luo Han Guo", "Lo Han Guo / Buah Biksu", "Monk Fruit", False, "unknown", "Paru-paru", "Suplemen herbal pereda tenggorokan dan batuk", "BPOM-TI"),
    ("片仔癀", "Pien Tze Huang", "Pien Tze Huang", "Pien Tze Huang", False, "unknown", "Hati", "Pereda radang dan infeksi pasca operasi", "BPOM-TI"),
    ("云南白药", "Yunnan Baiyao", "Yunnan Baiyao", "Yunnan Baiyao", False, "unknown", "Banyak", "Penghenti pendarahan, nyeri", "BPOM-TI"),
    ("人参", "Ren Shen", "Panax Ginseng", "Ginseng", False, "low", "Lien, Jantung", "Tonik kuat, tidak disarankan overdosis", "SM0012"),
    ("白果", "Bai Guo", "Ginkgo Biloba", "Ginkgo Nut", True, "low", "Paru, Ginjal", "Biji ginkgo biloba beracun ringan jika mentah", "SM0221"),
    ("复方阿胶浆", "Fu Fang E Jiao Jiang", "Fufang Ejiao Jiang", "- ", False, "unknown", "Darah", "Penambah darah", "BPOM-TI"),
    ("连花清瘟胶囊", "Lianhua Qingwen", "Lianhua Qingwen", "-", False, "unknown", "Paru", "Obat demam, flu, batuk", "BPOM-TI"),
    ("皮康霜", "Pi Kang Shuang", "Pi Kang Shuang", "-", False, "unknown", "Kulit", "Salep topikal pereda gatal", "BPOM-TI"),
    ("川贝枇杷膏", "Chuan Bei Pi Pa Gao", "Nin Jiom Pei Pa Koa", "Cough Syrup", False, "unknown", "Paru", "Meredakan batuk dan tenggorokan", "BPOM-TI"),
    ("天和骨通贴膏", "Tianhe Gutong", "Tianhe Koyo", "Pain Relief Patch", False, "unknown", "Kulit", "Koyo pegal dan rematik", "BPOM-TI"),
    ("步长脑心通", "Naoxintong", "Buchang Naoxintong", "Naoxintong Capsule", False, "unknown", "Jantung", "Memperlancar sirkulasi darah otak", "BPOM-TI"),
    ("安宫牛黄丸", "An Gong Niu Huang Wan", "An Gong Niu Huang", "Angong Pill", True, "moderate", "Jantung", "Mengandung cinnabar (merkuri sulfide) dalam resep asli. Hati-hati", "SM0111"),
    ("当归", "Dang Gui", "Dong Quai", "Angelica Root", False, "unknown", "Darah", "Suplemen darah untuk haid", "SM0034"),
    ("黄芪", "Huang Qi", "Astragalus", "Astragalus Root", False, "unknown", "Lien, Paru", "Meningkatkan daya tahan tubuh", "SM0056"),
    ("枸杞子", "Gou Qi Zi", "Goji Berry / Kici", "Goji Berry", False, "unknown", "Hati, Ginjal", "Kesehatan mata, antioksidan", "SM0078"),
    ("菊花", "Ju Hua", "Bunga Krisan", "Chrysanthemum", False, "unknown", "Hati, Paru", "Pereda panas dalam, mata merah", "SM0099"),
    ("冬虫夏草", "Dong Chong Xia Cao", "Cordyceps", "Cordyceps", False, "unknown", "Paru, Ginjal", "Meningkatkan fungsi pernapasan", "SM0100"),
    ("灵芝", "Ling Zhi", "Reishi Mushroom / Lingzhi", "Reishi", False, "unknown", "Jantung, Hati", "Stamina, fungsi ginjal", "SM0122"),
    ("燕窝", "Yan Wo", "Sarang Burung Walet", "Bird Nest", False, "unknown", "Paru", "Kesehatan kulit dan napas", "SM0134"),
    ("桃胶", "Tao Jiao", "Peach Gum", "Peach Resin", False, "unknown", "Kulit", "Kaya kolagen untuk dessert", "SM0155"),
    ("银耳", "Yin Er", "White Wood Ear / Jamur Es", "Silver Ear", False, "unknown", "Paru", "Meredakan batuk kering", "SM0166"),
    ("川贝母", "Chuan Bei Mu", "Chuan Bei Mu", "Fritillaria Bulb", False, "unknown", "Paru", "Ekspektoran penurun batuk", "SM0177"),
    ("跌打丸", "Tieh Ta Wan", "Tieh Ta Wan (Pil Memar)", "Trauma Pill", False, "unknown", "Otot", "Pereda bengkak akibat luka", "BPOM-TI"),
    ("正骨水", "Zheng Gu Shui", "Zheng Gu Shui", "Bone Setting Water", False, "unknown", "Otot", "Obat gosok urut patah tulang", "BPOM-TI"),
    ("山药", "Shan Yao", "Waisan", "Chinese Yam", False, "unknown", "Lien, Ginjal", "Memperbaiki fungsi pencernaan", "SM0199"),
    ("健脾丸", "Jian Pi Wan", "Kianpi / Jian Pi Wan", "Spleen Tonic", False, "unknown", "Lien", "Penambah berat badan", "BPOM-TI"),
    ("保济丸", "Bao Ji Wan", "Po Chai Pills / Bao Ji Wan", "Bao Ji Pills", False, "unknown", "Lambung", "Obat diare ringan", "BPOM-TI"),
    ("泰宾水", "Tai Bin Sui", "Tai Bin Sui", "Wasir", False, "unknown", "Usus", "Pereda wasir", "BPOM-TI"),
    ("龙胆泻肝汤", "Long Dan Xie Gan Tang", "Long Dan Xie Gan", "Gentian Decoction", True, "low", "Hati", "Hati-hati jika konsumsi jangka panjang jangka, efek samping ginjal ringan", "SM0222"),
    ("逍遥散", "Xiao Yao San", "Xiao Yao San", "Free Wanderer Powder", False, "unknown", "Hati", "Pereda stres, keluhan PMS", "SM0234"),
    ("六味地黄丸", "Liu Wei Di Huang Wan", "Liu Wei Di Huang Wan", "Six Flavor Rehmmania", False, "unknown", "Ginjal", "Mengobati kelemahan pinggang", "BPOM-TI"),
    ("马应龙", "Ma Ying Long", "Ma Ying Long", "Musk Hemorrhoid", False, "unknown", "Usus", "Salep wasir populer", "BPOM-TI"),
    ("藿香正气水", "Huo Xiang Zheng Qi Shui", "Huo Xiang Zheng Qi", "Huo Xiang Liquid", False, "unknown", "Lambung", "Obat pusing masuk angin", "BPOM-TI"),
    ("板蓝根", "Ban Lan Gen", "Banlangen", "Isatis Root", False, "unknown", "Tenggorokan", "Meredakan radang tenggorokan", "SM0333"),
    ("三金片", "San Jin Pian", "San Jin Pian", "-", False, "unknown", "Kandung Kemih", "Mengobati infeksi saluran kemih", "BPOM-TI"),
    ("红枣", "Hong Zao", "Kurma Merah / Angco", "Red Dates", False, "unknown", "Darah", "Tonik darah yang sangat umum", "SM0444"),
    ("黑枣", "Hei Zao", "Kurma Hitam", "Black Dates", False, "unknown", "Ginjal", "Tonik ginjal", "SM0445"),
    ("龙眼肉", "Long Yan Rou", "Daging Kelengkeng (Kering)", "Dried Longan", False, "unknown", "Jantung", "Konsumsi harian", "SM0446"),
    ("党参", "Dang Shen", "Codonopsis", "Codonopsis", False, "unknown", "Lien", "Alternatif ginseng yang lebih murah", "SM0447"),
    ("茯苓", "Fu Ling", "Poria", "Poria Mushroom", False, "unknown", "Lien", "Mengeluarkan kelembaban / air", "SM0448"),
    ("甘草", "Gan Cao", "Akar Manis / Licorice", "Licorice Root", False, "unknown", "Semua", "Pengharmonis ramuan lain, menetralkan racun", "SM0449"),
    ("八角", "Ba Jiao", "Bunga Lawang / Pekak", "Star Anise", False, "unknown", "Lambung", "Bumbu masak", "SM0450"),
    ("肉桂", "Rou Gui", "Kayu Manis", "Cinnamon", False, "unknown", "Ginjal", "Penghangat sirkulasi", "SM0451"),
    ("百合", "Bai He", "Lily Bulb", "Lily Bulb", False, "unknown", "Paru", "Moistens paru-paru", "SM0452"),
    ("莲子", "Lian Zi", "Biji Teratai", "Lotus Seed", False, "unknown", "Lien, Jantung", "Menghilangkan diare, tenang", "SM0453"),
    ("玉竹", "Yu Zhu", "Solomon Seal", "Solomon Seal", False, "unknown", "Paru, Lambung", "Tonik Yin", "SM0454"),
    ("麦冬", "Mai Dong", "Ophiopogon", "Ophiopogon", False, "unknown", "Paru", "Hasilkan cairan tubuh", "SM0455"),
    ("金银花", "Jin Yin Hua", "Bunga Honeysuckle", "Honeysuckle", False, "unknown", "Paru, Kulit", "Antibakteri kuat", "SM0456"),
    ("薄荷", "Bo He", "Peppermint", "Mint", False, "unknown", "Hati", "Membersihkan panas dan mata", "SM0457"),
    ("胖大海", "Pang Da Hai", "Kembang Semangkuk / Sea Coconut", "Sterculia Seed", False, "unknown", "Paru", "Obat suara serak, sakit tenggorokan", "SM0458"),
    ("杜仲", "Du Zhong", "Eucommia Bark", "Eucommia", False, "unknown", "Ginjal", "Tonik otot, sendi pinggang", "SM0459"),
    ("肉苁蓉", "Rou Cong Rong", "Cistanche", "Cistanche", False, "unknown", "Bowel", "Menambah cairan usus, laksatif", "SM0460"),
    ("菟丝子", "Tu Si Zi", "Dodder Seed", "Dodder Seed", False, "unknown", "Hati, Ginjal", "Memperbaiki kesuburan", "SM0461"),
    ("五味子", "Wu Wei Zi", "Schisandra Berry", "Schisandra", False, "unknown", "Paru", "Astringent obat batuk kronis", "SM0462"),
    ("熟地黄", "Shu Di Huang", "Rehmannia Matang", "Rehmannia", False, "unknown", "Ginjal", "Menutrisi darah kuat", "SM0463"),
    ("白芍", "Bai Shao", "Akar Peony Putih", "White Peony", False, "unknown", "Hati", "Pereda nyeri perut", "SM0464"),
    ("红花", "Hong Hua", "Safflower", "Safflower", True, "low", "Darah", "Melancarkan darah kuat, dikontraindikasi pada wanita hamil", "SM0465"),
    ("三七", "San Qi", "Notoginseng / Tienchi", "Notoginseng", False, "unknown", "Darah", "Menghentikan pendarahan mujarab", "SM0466"),
    ("柴胡", "Chai Hu", "Akar Bupleurum", "Bupleurum", False, "unknown", "Hati", "Perantara obat ke tubuh atas", "SM0467"),
    ("半夏", "Ban Xia", "Pinellia", "Pinellia Tuber", True, "low", "Paru, Lambung", "Mengusir dahak; mentah sangat beracun jadi harus diproses", "SM0468"),
    ("附子", "Fu Zi", "Aconite / Fu Zi", "Aconite Root", True, "high", "Jantung, Ginjal", "Sangat toksik mematikan jika tidak direbus lama. Toksin Aconitine menyebabkan henti jantung pendek.", "SM0999"),
    ("马钱子", "Ma Qian Zi", "Biji Strychni / Nux Vomica", "Strychnos Seed", True, "high", "Saraf", "Mengandung strichnina, menstimulasi sistem saraf, mudah over dosis", "SM0998"),
    ("朱砂", "Zhu Sha", "Cinnabar (Sulfida Merkuri)", "Cinnabar", True, "high", "Sistem Tubuh", "Hanya dipakai di obat darurat luar batas kewajaran obat harian", "SM0997"),
    ("雄黄", "Xiong Huang", "Realgar (Sulfida Arsenik)", "Realgar", True, "high", "Sistem Tubuh", "Toksisitas merkuri / arsenik", "SM0996"),
    ("斑蝥", "Ban Mao", "Kumbang Mylabris", "Mylabris", True, "high", "Kulit", "Mempunyai kantharidin untuk obat kanker spesifik, efek melepuh", "SM0995"),
    ("巴豆", "Ba Dou", "Kroton", "Croton Seed", True, "high", "Usus", "Pencahar drastis berbisa tinggi", "SM0994"),
    ("甘遂", "Gan Sui", "Kan Sui", "Euphorbia Kansui", True, "moderate", "Ginjal", "Menyebabkan dehidrasi parah", "SM0993"),
    ("天南星", "Tian Nan Xing", "Jack in the Pulpit Tuber", "Arisaema", True, "low", "Paru", "Menghilangkan dahak, pemrosesan wajib", "SM0992"),
    ("细辛", "Xi Xin", "Wild Ginger / Xi Xin", "Asarum", True, "low", "Ginjal, Paru", "Asam aristolokat berefek gagal ginjal", "SM0991"),
    ("关木通", "Guan Mu Tong", "Guan Mu Tong", "Aristolochia Manshuriensis", True, "high", "Ginjal", "Memicu kanker uriner dan gagal ginjal", "SM0990"),
    ("防己", "Fang Ji", "Akar Stephania", "Stephania", True, "moderate", "Ginjal", "Sering tertukar, mengandung toksin saraf ringan", "SM0989"),
    ("何首乌", "He Shou Wu", "Fallopia Multifora (Kacang Kenari)", "Fleeceflower Root", True, "low", "Hati", "Pemakaian tak tepat picu radang hati (Hepatitis)", "SM0988"),
    ("苦参", "Ku Shen", "Sophora Root", "Sophora", False, "unknown", "Usus", "Pembersih panas usus", "SM0880"),
    ("黄连", "Huang Lian", "Akar Coptis", "Coptis Root", False, "unknown", "Jantung", "Obat anti-bakteri saluran cerna kuat", "SM0881"),
    ("苍术", "Cang Zhu", "Cang Zhu", "Atractylodes", False, "unknown", "Lien", "Mengeringkan kelembaban berlebih", "SM0882"),
    ("厚朴", "Hou Po", "Kulit Magnolia", "Magnolia Bark", False, "unknown", "Lambung", "Melancarkan qi perut kembung", "SM0883"),
    ("陈皮", "Chen Pi", "Kulit Jeruk Kering (Tangerine)", "Tangerine Peel", False, "unknown", "Paru, Lambung", "Mengusir riak lendir", "SM0884"),
    ("枳实", "Zhi Shi", "Jeruk Pahit Mentah", "Immature Bitter Orange", False, "unknown", "Lien", "Pemecah perut mual dan sembelit", "SM0885"),
    ("麦芽", "Mai Ya", "Kecambah Barley", "Barley Sprout", False, "unknown", "Lambung", "Mencerna makanan pati", "SM0886"),
    ("当归尾", "Dang Gui Wei", "Ujung Angelica", "Angelica Root Tip", False, "unknown", "Darah", "Melancarkan pembekuan darah", "SM0887"),
    ("川芎", "Chuan Xiong", "Chuan Xiong", "Szechuan Lovage", False, "unknown", "Kepala", "Obat migrain nomer satu TCM", "SM0888"),
    ("延胡索", "Yan Hu Suo", "Akar Corydalis", "Corydalis", False, "unknown", "Hati", "Obat penghilang nyeri setara herbal aspirin", "SM0889"),
    ("牛膝", "Niu Xi", "Akar Achyranthes", "Achyranthes", False, "unknown", "Kaki", "Memandu obat ke pinggang dan lutut belakang", "SM0890"),
    ("桑枝", "Sang Zhi", "Ranting Mulberry", "Mulberry Twig", False, "unknown", "Sendi", "Nyeri sendi tangan", "SM0891"),
    ("独活", "Du Huo", "Akar Angelica Pubescentis", "Pubescent Angelica", False, "unknown", "Sendi Bawah", "Nyeri sendi punggung dan kaki", "SM0892"),
    ("木瓜", "Mu Gua", "Pepaya Cina Tradisional", "Chaenomeles", False, "unknown", "Otot", "Kram betis", "SM0893"),
    ("酸枣仁", "Suan Zao Ren", "Biji Ziziphus / Jujube Liar", "Sour Jujube Seed", False, "unknown", "Jantung, Hati", "Menenangkan hati dan susana pikiran curiga", "SM0894"),
    ("柏子仁", "Bai Zi Ren", "Biji Biota", "Arborvitae Seed", False, "unknown", "Jantung", "Hati gelisah berdebar", "SM0895"),
    ("钩藤", "Gou Teng", "Uncaria, Gambir", "Uncaria Vine", False, "unknown", "Hati", "Demam kejang pada hipertensi", "SM0896"),
    ("天麻", "Tian Ma", "Gastrodia", "Gastrodia Root", False, "unknown", "Hati", "Vertigo akut dan kronis", "SM0897"),
    ("葛根", "Ge Gen", "Akar Kudzu", "Kudzu Root", False, "unknown", "Leher", "Ketegangan otot leher", "SM0898"),
    ("升麻", "Sheng Ma", "Akar Cimicifuga", "Bugbane Rhizome", False, "unknown", "Energi", "Mengangkat rahim turun", "SM0899"),
    ("牛蒡子", "Niu Bang Zi", "Biji Burdock", "Burdock Seed", False, "unknown", "Tenggorokan", "Sakit tenggorokan panas kronik", "SM0900"),
    ("桔梗", "Jie Geng", "Akar Platycodon", "Balloon Flower Root", False, "unknown", "Paru", "Membawa obat radang ke paruparu atas", "SM0901"),
    ("白芷", "Bai Zhi", "Angelica Dahurica", "Angelica Dahurica", False, "unknown", "Kepala", "Sakit kepala sinus hidung", "SM0902"),
    ("紫苏叶", "Zi Su Ye", "Daun Perilla", "Perilla Leaf", False, "unknown", "Paru", "Alergi dan flu biasa karena dingin", "SM0903"),
    ("荆芥", "Jing Jie", "Schizonepeta", "Schizonepeta", False, "unknown", "Kulit", "Gatal-gatal di tahap awal", "SM0904"),
    ("防风", "Fang Feng", "Akar Saposhnikovia", "Ledebouriella Root", False, "unknown", "Semua", "Mengusir virus flu luar", "SM0905"),
    ("石膏", "Shi Gao", "Gypsum Fibrosum", "Gypsum", False, "unknown", "Paru, Lambung", "Pereda demam suhu tinggi super kencang", "SM0906"),
    ("冬瓜皮", "Dong Gua Pi", "Kulit Labu Air", "Winter Melon Peel", False, "unknown", "Kulit", "Edema (Bengkak air)", "SM0907"),
    ("地肤子", "Di Fu Zi", "Biji Kochia", "Kochia Seed", False, "unknown", "Kulit", "Luka basah / borok", "SM0908")
]

async def seed_data():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
    db = client.get_database(os.getenv("MONGODB_DB_NAME", "fitmate_db"))
    collection = db["tcm_ingredients"]

    await collection.create_index("mandarin_name", unique=True)

    inserted = 0
    errors = 0
    for item in POPULAR_TCM:
        mandarin, pinyin, indo, eng, is_toxic, tox_level, org, desc, ref = item

        record = {
            "mandarin_name": mandarin,
            "pinyin_name": pinyin,
            "indonesian_name": indo,
            "english_name": eng,
            "is_toxic": is_toxic,
            "toxicity_level": tox_level,
            "target_organ": org,
            "description": desc,
            "source_reference": ref,
            "validated_by": "direct_seed"
        }

        try:
            ingredient = TCMIngredient(**record)
            await collection.update_one(
                {"mandarin_name": ingredient.mandarin_name},
                {"$set": ingredient.model_dump()},
                upsert=True,
            )
            inserted += 1
        except ValidationError as e:
            print(f"Error on {indo}: {e}")
            errors += 1

    print(f"Done database seeding. Inserted/Updated {inserted} records. Errors: {errors}.")

if __name__ == "__main__":
    asyncio.run(seed_data())
