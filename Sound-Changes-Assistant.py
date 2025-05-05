from flask import Flask, render_template, request, jsonify
from zemberek import TurkishSpellChecker
from zemberek import TurkishMorphology
import os

app = Flask(__name__)

morphology = TurkishMorphology.create_with_defaults()
spell_checker = TurkishSpellChecker(morphology)


detected_sound_changes = []

sesli_harfler = ["a", "e", "ı", "i", "o", "ö", "u", "ü"]
sessiz_harfler = ["z", "y", "v", "t", "ş", "s", "r", "p", "n", "m", "l", "k", "h", "j", "ğ", "g", "f", "d", "ç", "c", "b"]
fiil_cekim_ekleri = ["dı","di","du","dü", "tı","ti","tu","tü", "mış","miş","muş","müş", "yor", "acak","ecek", "r", "er","ar","ır","ir","ur","ür","se","sa","a"]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/suggest', methods=['GET'])
def suggest():
    query = request.args.get('q', '').lower()  # Get query from the request and convert to lowercase
    if len(query) < 3:  # Only provide suggestions if the query is 3+ characters long
        return jsonify([])  # Return an empty list if the query is too short
    
    suggestions = get_suggestions(query)
    return jsonify(suggestions)

@app.route('/process', methods=['POST'])
def process():
    global detected_sound_changes  
    
    detected_sound_changes.clear()
    
    user_input = request.form.get('user_input')
    results = analyze_word(user_input)

    display_results = [
      {
          "root": result["root"],
          "normalized_root": result["normalized_root"],
          "suffixes": result["suffixes"],
          "analysis": str(result["analysis"]),
          "sound_events": detect_ses_olaylari(result),
          "suffix_kinds": result["find_suffix_kinds"][0],
          "suffix_display": result["find_suffix_kinds"][1][::-1]
      }
      for result in results
    ]
    
    return jsonify(result=display_results if display_results else "No result found")


def analyze_word(word):
    analysis = morphology.analyze(word)
    results = []

    if analysis.analysis_results:
        first_result = analysis.analysis_results[0]
        root = first_result.get_stem()
        suffixes = first_result.get_ending()
        normalized_root = str(first_result).split(":")[0][1:]

        results.append({
            'root': root,
            'normalized_root': normalized_root,
            'suffixes': suffixes,
            "analysis": analysis,
            "find_suffix_kinds": find_suffix_kinds(root,normalized_root,suffixes,word, analysis)
        })
    return results

def get_suggestions(query):
    suggestions = spell_checker.suggest_for_word(query)
    return [suggestion for suggestion in suggestions]

def detect_ses_olaylari(result):
    global detected_sound_changes  

    root = result['root']
    suffixed_word = result['suffixes']
    normalized_root = result['normalized_root']
    input_word = request.form.get('user_input')
    analysis = result["analysis"]


    checks = [
        check_unsuz_yumusamasi,
        check_unlu_daralmasi,
        check_unlu_dusmesi,
        check_kaynastirma_harfleri,
        check_unlu_turemesi,
        check_unsuz_sertlesmesi,
        check_unsuz_dusmesi,
        check_unsuz_turemesi
    ]

    for check in checks:
        try:
            result = check(root, suffixed_word, normalized_root, input_word, analysis)
            if result:
                detected_sound_changes.append(result)
        except Exception as e:
            print(f"Error in {check.__name__}: {e}")

    return detected_sound_changes



def check_unsuz_turemesi(root, suffixed_word, normalized_root, input_word, analysis_results):   
    for i in range(1, len(root)):
        if root[i-1] == root[i] and root[i] in sessiz_harfler:
            return "Ünsüz Türemesi"
        

    return None


def check_unsuz_yumusamasi(root, suffixed_word, normalized_root, input_word, analysis_results):
    hard_to_soft = {'b': 'p', 'c': 'ç', 'd': 't', 'ğ': 'k'}
    hard_to_soft_real = {'p': 'b', 'ç': 'c', 't': 'd', 'k': 'ğ'}
    
    if root[-1] in hard_to_soft and input_word.startswith(root[:-1] + hard_to_soft_real[hard_to_soft[root[-1]]]):
        
        return "Ünsüz Yumuşaması"
    return None

def check_unlu_daralmasi(root, suffixed_word, normalized_root, input_word, analysis_results):
    if len(normalized_root) < len(root):
        return None
    if len(root) == len(normalized_root) or len(root)+1 == len(normalized_root):
        return None
    elif normalized_root[len(root)] not in 'ae' and normalized_root[len(root)+1] not in 'ae':
        return None
    if (normalized_root == "demek" or normalized_root == "yemek") and (input_word.startswith("di") or input_word.startswith("yi")):
        
        return "Ünlü Daralması"
    narrowing_rules = {
        'a': {'ı', 'i', 'u', 'ü'},
        'e': {'ı', 'i', 'u', 'ü'}
    }

    if suffixed_word[:2] in {"mı", "mi", "mu", "mü"}:
        if suffixed_word[1] in narrowing_rules[normalized_root[len(root)+1]]:
            
            return "Ünlü Daralması"
    if normalized_root[len(root)] in narrowing_rules:
        narrowed_vowel = suffixed_word[0] if suffixed_word[0] in narrowing_rules[normalized_root[len(root)]] else None
    else:
        return None
    if narrowed_vowel:
        
        return "Ünlü Daralması"
    return None



def check_unlu_dusmesi(root, suffixed_word, normalized_root, input_word, analysis_results):
    if "Ünsüz Yumuşaması" in detected_sound_changes or "Ünsüz Türemesi" in detected_sound_changes:
        return None
    if len(normalized_root) < len(root):
        return None
    known_istisna = [
        "kahvaltı", "niçin", "nasıl", "sütlâç", "güllâç", 
        "cumartesi", "pazartesi", "oynamak", "ilerlemek", 
        "sararmak", "koklamak", "yumurtlamak",
        "sızlamak", "buyruk", "kavşak", "kıvrım", "uyku", 
        "çevre", "yalnız", "kaynana"
    ]
    known_suffix = ["yle", "le", "yla", "la", "sa", "se", "ti", "di", "yse", "ysa", "tı", "dı", "miş", "mış", "dü", "du", "dı"]
    for i in range(len(analysis_results.analysis_results)):
        first_result_ = analysis_results.analysis_results[i]
        root_ = first_result_.get_stem()
        suffixes_ = first_result_.get_ending()
        normalized_root_ = str(first_result_).split(":")[0][1:]
        for i in range(len(root_)):
            if root_[i] in sessiz_harfler and normalized_root_[i] in sesli_harfler:
                
                return "Ünlü Düşmesi"
    if normalized_root != "etmek" and normalized_root != "et" and normalized_root.endswith("etmek"):
        
        return "Ünlü Düşmesi"
    if normalized_root != "olmak" and normalized_root != "ol" and normalized_root.endswith("olmak"):
        
        return "Ünlü Düşmesi"
    if normalized_root in known_istisna:
        
        return "Ünlü Düşmesi"    
    for i in range(len(analysis_results.analysis_results)):
        if (input_word[-2:] in known_suffix or input_word[-3:] in known_suffix) and not any(":Verb" in str(result) for result in analysis_results):
            
            return "Ünlü Düşmesi"
        
            
    return None





# this function needs fix!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! maybe implement ş and s, and also it fails on some of them like ; Kök: öyle, Asıl kök: öyle, Ekler: ydi, Ses Olayları: ['Ünlü Düşmesi']
def check_kaynastirma_harfleri(root, suffixes, normalized_root, word, analysis_results):
    vowels = "aeıioöuü"
    buffer_y_suffixes = ["ya", "yı", "ye", "yu", "yi", "yip", "yince"]
    buffer_n_suffixes = ["nda", "nde", "nı", "ni", "nun", "nin", "nın", "nün"]
    known_suffixes = ["şer", "şar", "sı", "si", "sız", "se", "ydi", "ye"]

    suffix_string = ''.join(suffixes)
    
    for suffix in known_suffixes:
        if word.endswith(suffix):
            return "Kaynaştırma Ünsüzü"
    
    if root[-1] in vowels and any(suffix_string.startswith(suffix) for suffix in buffer_y_suffixes):
        return "Kaynaştırma Harfi"
    
    if any(suffix_string.startswith(suffix) for suffix in buffer_n_suffixes):
        return "Kaynaştırma Harfi"

    return None





def check_unsuz_dusmesi(root, suffixed_word, normalized_root, input_word, analysis_results):
    consonant_drop_suffixes = ["cik", "cek", "cık", "cak", "cuk", "cük", "çik", "çık", "çek", "çak"]
    for suffix in consonant_drop_suffixes:
        if root.endswith(suffix):
            possible_root = root[:-len(suffix)] + "k"
            
            if is_actual_word(possible_root):
                return "Ünsüz Düşmesi"

    return False  


def check_unlu_turemesi(root, suffixed_word, normalized_root, input_word, analysis_results):
    if "Ünsüz Düşmesi" in detected_sound_changes:
        return None
    diminutive_suffixes = ["cik", "cık", "cuk", "cük"]
    
    for suffix in diminutive_suffixes:
        if input_word.endswith(suffix) and input_word.startswith(root):
            insertion_point = len(input_word) - len(suffix)
            if root[-1] not in "aeıioöuü" and input_word[insertion_point - 1] in "aeıioöuü":
                
                return "Ünlü Türemesi"

    intensifier_prefixes = ["sapa", "güpe", "çapa", "çepe", "apa", "düpe"]
    
    is_verb = any("Verb" in str(result) for result in analysis_results)
    if is_verb:
        for suffix in ["dur", "edur", "adur"]:  
            if input_word.endswith(suffix):
                base_word = input_word[:-len(suffix)]
                if base_word == root:
                    
                    return "Ünlü Türemesi"

    for prefix in intensifier_prefixes:
        if input_word.startswith(prefix):
            
            return "Ünlü Türemesi"
    
    return None


def check_unsuz_sertlesmesi(root, suffixed_word, normalized_root, input_word, analysis_results):
    hardening_consonants = "çtk"
    hard_consonants = "pçtkfşsh"
    last_letter = input_word[0]
    for letter in input_word[1:]:
        if last_letter in hard_consonants and letter in hardening_consonants:
            
            return "Ünsüz Sertleşmesi"
        last_letter = letter
    
    return None

def check_unlu_degisimi(root, suffixed_word, normalized_root, input_word, analysis_results):
    if input_word == "sana" or input_word == "bana":
        return "Ünlü Değişimi"


def is_actual_word(word):
    analysis = morphology.analyze(word)
    if analysis.analysis_results and not any(":Verb" in str(result) for result in analysis.analysis_results):
        return True


def find_suffix_kinds(root, suffixed_word, normalized_root, input_word, analysis_results):
    suffix_kinds = []
    result_str = str(analysis_results.analysis_results[0])
    answer = []
    
    suffix_translation = {
        # === Your Original Entries (Preserved) ===
        "Verb": "Fiil",
        "Noun": "İsim",
        "Adj": "Sıfat",
        "Adv": "Zarf",
        "Neg": "Negatif Eki",
        "Past": "Bilinen Geçmiş Zaman Eki",
        "Fut": "Gelecek Zaman Eki",
        "Prog": "Şimdiki Zaman Eki",
        "Cond": "Koşul-Şart Eki",
        "A1sg": "Birinci Tekil Şahıs (Ben)",
        "A2sg": "İkinci Tekil Şahıs (Sen)",
        "Acc": "Belirtme Hâl Eki",
        "Dat": "Yönelme Hâl Eki",
        "A3pl": "Üçüncü Çoğul Kişi (Onlar)",
        "A1pl": "Birinci Çoğul Kişi (Biz)",
        "A2pl": "İkinci Çoğul Kişi (Siz)",
        "Opt": "İstek Kip Eki",
        "Aor": "Geniş Zaman Eki",
        "Pass": "Edilgen Eki",
        "Neces": "Gereklilik Eki",
        "Imp": "Emir Kipi Eki",
        "Desr": "İstek Kip Eki",
        "While": "Zarf-Fiil Eki",
        "AfterDoingSo": "Zarf-Fiil Eki",
        "ByDoingSo": "Zarf-Fiil Eki",
        "WithoutHavingDoneSo": "Zarf-Fiil Eki",
        "AsLongAs": "Zarf-Fiil Eki",
        "When": "Zarf-Fiil Eki",
        "SinceDoingSo": "Zarf-Fiil Eki",
        "Adamantly": "Zarf-Fiil Eki",
        "AsIf": "Zarf-Fiil Eki",
        "Postp": "Edat",
        "P1sg": "Birinci Tekil Şahıs İyelik Eki",
        "Agt": "Etken Kişi Eki",
        "P2sg": "İkinci Tekil Şahıs İyelik Eki",
        "Gen": "İyelik Eki / Tamlayan Eki",
        "Equ": "Eşitlik Hâl Eki",
        "P3sg": "Üçüncü Tekil Şahıs İyelik Eki",
        "P1pl": "Birinci Çoğul Şahıs İyelik Eki",
        "P2pl": "İkinci Çoğul Şahıs İyelik Eki",
        "P3pl": "Üçüncü Çoğul Şahıs İyelik Eki",
        "Loc": "Bulunma hâli (-da/-de)",
        "Without": "Yoksunluk eki (-sız/-siz)",

        # === New Additions (Expanded Coverage) ===
        # POS Tags
        "Pron": "Zamir",
        "Num": "Sayı",
        "Det": "Belirteç",
        "Interj": "Ünlem",
        "Conj": "Bağlaç",
        "Ques": "Soru Eki (mı/mi/mu/mü)",
        "Dup": "İkileme",
        "Prop": "Özel İsim",
        "Abbr": "Kısaltma",
        
        # Case Markers
        "Nom": "Yalın hâl",
        "Abl": "Ayrılma hâli (-dan/-den)",
        "Ins": "Vasıta hâli (-la/-le)",
        
        # Person/Number
        
        # Possessive
        
        # Tense/Aspect
        "Pres": "Geniş Zaman",
        "Narr": "Duyulan Geçmiş Zaman (-mış/-miş)",  # Enhanced
        
        # Mood
        "Coh": "İstek Kipi (Şartlı)",
        
        # Voice
        "Reflex": "Dönüşlü Çatı (-n)",
        "Recip": "İşteş Çatı (-ış/-iş)",
        "Coop": "İşbirliği Çatı (-laş/-leş)",
        
        # Verbals
        "Inf": "İsim-Fiil (-mak/-mek)",
        "Part": "Sıfat-Fiil (-an/-en/-dık/-dik)",
        "Ger": "Zarf-Fiil (-ip/-erek/-ken)",
        
        # Derivational
        "Dim": "Küçültme Eki (-cık/-cik)",
        "Prof": "Meslek Eki (-cı/-ci)",
        "With": "Birliktelik Eki (-lı/-li)",
        "FutPart": "Gelecek Zaman Ortacı (-acak/-ecek)",
        
        # Rare/Technical
        "Able": "Yeterlilik Kipi (-ebil/-abil)",
        "Almost": "Yaklaşma Eki (-eyaz-)",
        "JustLike": "Benzetme Eki (-gil)",
        "Start": "Başlama Eki (-a/-e)",
        "Stay": "Kalma Eki (-a/-e)",
        "Repeat": "Tekrar Eki (-a/-e)",
        
        # Compound
        "Comp": "Birleşik Sözcük",
        "Acquire": "Kazanma Eki (-lan/-len)",
        "Become": "Olma Eki (-laş/-leş)",
        
        # Special
        "Card": "Asıl Sayı",
        "Dist": "Üleştirme (-ar/-er)",
        "Ord": "Sıra Sayı (-ıncı/-inci)",
        "Range": "Aralık (-ar/-er)",
        "Ratio": "Oran (-ca/-ce)",
        "Real": "Gerçeklik Eki (-dir)"
    }
    
    

    suffix_part = result_str.split("]")[1][1:]
    suffixes = "".join(suffix_part)
    concurrent_word = ""
    for index, i in enumerate(suffixes):
        concurrent_word += i
        if i == "+" or i == ":":
            concurrent_word = ""
            continue
        if concurrent_word in suffix_translation:
            suffix_kinds.append(concurrent_word)
            
    translated_suffix_kinds = [suffix_translation[i] for i in suffix_kinds]
    answer.append(translated_suffix_kinds)
    
    
    
    get_letter = False
    concurrent_word = ""
    display_word = ""
    for i in suffixes[::-1]:
        if get_letter:
            concurrent_word += i
        if i == "+":
            get_letter = False
            if concurrent_word:
                display_word += concurrent_word
        if i == "|":
            get_letter = False
            if concurrent_word:
                display_word += concurrent_word
        if i == ":":
            get_letter = True
    answer.append(concurrent_word)
    return answer
    


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  
    app.run(host="0.0.0.0", port=port, debug=False)
